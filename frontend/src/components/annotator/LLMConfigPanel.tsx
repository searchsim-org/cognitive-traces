'use client'

import { useState, useEffect } from 'react'
import { Eye, EyeOff, Save, Key, Brain, RefreshCw, Server, CheckCircle, XCircle, Settings, Zap, FileText, AlertCircle, Info, HelpCircle, Loader2 } from 'lucide-react'
import { api } from '@/lib/api'
import toast from 'react-hot-toast'

// Dynamic import for crypto-js to avoid SSR issues
let CryptoJS: any = null
if (typeof window !== 'undefined') {
  import('crypto-js').then(module => {
    CryptoJS = module.default
  })
}

interface LLMConfigPanelProps {
  onConfigComplete: (config: LLMConfig) => void
}

interface LLMConfig {
  // Model selection
  analyst_model: string
  critic_model: string
  judge_model: string
  
  // API keys
  anthropic_api_key?: string
  openai_api_key?: string
  google_api_key?: string
  ollama_base_url?: string
  
  // Custom endpoints
  custom_endpoints?: CustomEndpoint[]
  
  // Fallback configuration
  enable_fallback?: boolean
  fallback_analyst_model?: string
  fallback_critic_model?: string
  fallback_judge_model?: string
  fallback_retry_after?: number  // Minutes to retry custom endpoint
  
  // Session handling
  session_strategy?: 'truncate' | 'sliding_window' | 'full'
  window_size?: number
  
  // Model parameters
  temperature?: number
  max_tokens_base?: number
  max_tokens_cap?: number
  tokens_per_event?: number
  
  // Truncation limits
  truncate_content_small?: number
  truncate_content_medium?: number
  truncate_content_large?: number
  truncate_reasoning_small?: number
  truncate_reasoning_medium?: number
  truncate_reasoning_large?: number
  
  // Custom prompts
  analyst_prompt_override?: string | null
  critic_prompt_override?: string | null
  judge_prompt_override?: string | null
}

interface CustomEndpoint {
  id: string
  name: string
  base_url: string
  api_key: string
  models?: ModelInfo[]
  connected?: boolean
}

interface ModelInfo {
  id: string
  name: string
  provider: string
  description: string
  context_window: number
  cost: string
  recommended: boolean
}

interface ModelCapabilities {
  maxTokens: number
  contextWindow: number
  supportsTemperature: boolean
  temperatureRange: [number, number]
  recommendedTemperature: number
}

// Simple encryption key (in production, use a more secure method)
const ENCRYPTION_KEY = 'cognitive-traces-key-v1'

export function LLMConfigPanel({ onConfigComplete }: LLMConfigPanelProps) {
  const [config, setConfig] = useState<LLMConfig>({
    // Model selection
    analyst_model: 'claude-3-5-sonnet-20241022',
    critic_model: 'gpt-4o',
    judge_model: 'gpt-4o',
    
    // API keys
    anthropic_api_key: '',
    openai_api_key: '',
    google_api_key: '',
    ollama_base_url: 'http://localhost:11434',
    
    // Custom endpoints
    custom_endpoints: [],
    
    // Fallback configuration
    enable_fallback: false,
    fallback_analyst_model: 'gpt-4o-mini',
    fallback_critic_model: 'gpt-4o-mini',
    fallback_judge_model: 'gpt-4o-mini',
    fallback_retry_after: 5,  // 5 minutes
    
    // Session handling (defaults)
    session_strategy: 'truncate',
    window_size: 30,
    
    // Model parameters (defaults)
    temperature: 0.7,
    max_tokens_base: 4096,
    max_tokens_cap: 16000,
    tokens_per_event: 100,
    
    // Truncation limits (defaults)
    truncate_content_small: 200,
    truncate_content_medium: 150,
    truncate_content_large: 100,
    truncate_reasoning_small: 300,
    truncate_reasoning_medium: 200,
    truncate_reasoning_large: 150,
    
    // Custom prompts
    analyst_prompt_override: null,
    critic_prompt_override: null,
    judge_prompt_override: null,
  })

  const [showKeys, setShowKeys] = useState({
    anthropic: false,
    openai: false,
    google: false,
  })

  const [availableModels, setAvailableModels] = useState<{
    anthropic: ModelInfo[]
    openai: ModelInfo[]
    google: ModelInfo[]
    ollama: ModelInfo[]
    custom: ModelInfo[]
  }>({
    anthropic: [],
    openai: [],
    google: [],
    ollama: [],
    custom: [],
  })

  const [isLoadingModels, setIsLoadingModels] = useState(false)
  const [ollamaConnected, setOllamaConnected] = useState(false)
  const [isSaved, setIsSaved] = useState(false)
  const [activeTab, setActiveTab] = useState<'models' | 'strategy' | 'parameters' | 'prompts'>('models')
  const [defaultPrompts, setDefaultPrompts] = useState<any>(null)
  const [currentPrompts, setCurrentPrompts] = useState<any>(null)
  const [showProviderTooltip, setShowProviderTooltip] = useState(false)
  
  // Custom endpoint state
  const [showCustomEndpointForm, setShowCustomEndpointForm] = useState(false)
  const [newEndpoint, setNewEndpoint] = useState({ name: '', base_url: '', api_key: '' })
  const [isTestingEndpoint, setIsTestingEndpoint] = useState(false)

  // Encryption/Decryption functions
  const encrypt = (text: string): string => {
    if (!CryptoJS) return text // Fallback if crypto not loaded yet
    return CryptoJS.AES.encrypt(text, ENCRYPTION_KEY).toString()
  }

  const decrypt = (ciphertext: string): string => {
    if (!CryptoJS) return ciphertext // Fallback if crypto not loaded yet
    try {
      const bytes = CryptoJS.AES.decrypt(ciphertext, ENCRYPTION_KEY)
      return bytes.toString(CryptoJS.enc.Utf8)
    } catch {
      return ''
    }
  }

  // Load saved API keys on mount
  useEffect(() => {
    const savedAnthropicKey = localStorage.getItem('encrypted_anthropic_key')
    const savedOpenAIKey = localStorage.getItem('encrypted_openai_key')
    const savedGoogleKey = localStorage.getItem('encrypted_google_key')
    const savedOllamaUrl = localStorage.getItem('ollama_base_url')

    if (savedAnthropicKey) {
      setConfig(prev => ({ ...prev, anthropic_api_key: decrypt(savedAnthropicKey) }))
    }
    if (savedOpenAIKey) {
      setConfig(prev => ({ ...prev, openai_api_key: decrypt(savedOpenAIKey) }))
    }
    if (savedGoogleKey) {
      setConfig(prev => ({ ...prev, google_api_key: decrypt(savedGoogleKey) }))
    }
    if (savedOllamaUrl) {
      setConfig(prev => ({ ...prev, ollama_base_url: savedOllamaUrl }))
    }

    // Load models initially
    loadAvailableModels()
  }, [])

  const loadAvailableModels = async () => {
    setIsLoadingModels(true)
    try {
      const response = await api.getAvailableModels({
        include_ollama: true,
        ollama_url: config.ollama_base_url,
      })
      
      const models = response.data.models
      // Preserve custom models when updating from API
      setAvailableModels(prev => ({
        ...models,
        custom: prev.custom || []  // Keep existing custom models
      }))
      setOllamaConnected(models.ollama && models.ollama.length > 0)
    } catch (error) {
      console.error('Error loading models:', error)
      toast.error('Failed to load available models')
    } finally {
      setIsLoadingModels(false)
    }
  }

  const testOllamaConnection = async () => {
    setIsLoadingModels(true)
    try {
      const response = await api.getOllamaModels(config.ollama_base_url)
      const models = response.data.models
      
      if (models.length > 0) {
        setOllamaConnected(true)
        // Preserve custom models when updating ollama
        setAvailableModels(prev => ({ ...prev, ollama: models }))
        toast.success(`Connected! Found ${models.length} Ollama models`)
      } else {
        setOllamaConnected(false)
        toast.error('Ollama is running but no models found')
      }
    } catch (error) {
      setOllamaConnected(false)
      toast.error('Could not connect to Ollama. Make sure it\'s running.')
    } finally {
      setIsLoadingModels(false)
    }
  }

  const loadDefaultPrompts = async () => {
    try {
      const response = await api.get('/annotations/config/prompts')
      setDefaultPrompts(response.data)
      // Pre-populate current prompts if not overridden
      if (!config.analyst_prompt_override) {
        setCurrentPrompts({
          analyst: response.data.analyst_prompt,
          critic: response.data.critic_prompt,
          judge: response.data.judge_prompt
        })
      }
    } catch (error) {
      console.error('Error loading default prompts:', error)
      toast.error('Failed to load default prompts')
    }
  }

  // Test and add custom endpoint
  const testCustomEndpoint = async () => {
    if (!newEndpoint.base_url || !newEndpoint.name) {
      toast.error('Please provide endpoint name and URL')
      return
    }

    setIsTestingEndpoint(true)
    try {
      // Use backend proxy to avoid CORS issues
      const params = new URLSearchParams({
        base_url: newEndpoint.base_url
      })
      
      if (newEndpoint.api_key) {
        params.append('api_key', newEndpoint.api_key)
      }

      const response = await api.post(`/models/custom/test?${params.toString()}`)
      const data = response.data

      if (!data.success || !data.models || data.models.length === 0) {
        toast.error('No models found at this endpoint')
        return
      }

      // Convert to ModelInfo format
      const modelInfos: ModelInfo[] = data.models.map((model: any) => ({
        id: model.id,
        name: model.name || model.id,
        provider: 'custom',
        description: model.description || `Custom model from ${newEndpoint.name}`,
        contextWindow: model.contextWindow || 8192,
      }))

      // Add endpoint to config
      const endpointId = `custom_${Date.now()}`
      const endpoint: CustomEndpoint = {
        id: endpointId,
        name: newEndpoint.name,
        base_url: data.base_url || newEndpoint.base_url,
        api_key: newEndpoint.api_key,
        models: modelInfos,
        connected: true,
      }

      // Prepare updated endpoints
      const updatedEndpoints = [...(config.custom_endpoints || []), endpoint]
      
      // Update config
      setConfig(prev => ({
        ...prev,
        custom_endpoints: updatedEndpoints
      }))

      // Add models to available models
      const allCustomModels = updatedEndpoints.flatMap(e => e.models || [])
      setAvailableModels(prev => ({
        ...prev,
        custom: allCustomModels
      }))

      // Save to localStorage
      localStorage.setItem('custom_endpoints', JSON.stringify(updatedEndpoints))

      toast.success(`Connected! Found ${data.models.length} models`)
      setShowCustomEndpointForm(false)
      setNewEndpoint({ name: '', base_url: '', api_key: '' })
    } catch (error: any) {
      console.error('Error testing custom endpoint:', error)
      const message = error.response?.data?.detail || error.message || 'Unknown error'
      toast.error(`Failed to connect: ${message}`)
    } finally {
      setIsTestingEndpoint(false)
    }
  }

  const removeCustomEndpoint = (endpointId: string) => {
    const updatedEndpoints = (config.custom_endpoints || []).filter(e => e.id !== endpointId)
    setConfig(prev => ({ ...prev, custom_endpoints: updatedEndpoints }))
    
    // Reload custom models
    const allCustomModels = updatedEndpoints.flatMap(e => e.models || [])
    setAvailableModels(prev => ({ ...prev, custom: allCustomModels }))
    
    // Update localStorage
    localStorage.setItem('custom_endpoints', JSON.stringify(updatedEndpoints))
    toast.success('Endpoint removed')
  }

  // Load custom endpoints from localStorage on mount
  useEffect(() => {
    const savedEndpoints = localStorage.getItem('custom_endpoints')
    
    if (savedEndpoints) {
      try {
        const endpoints: CustomEndpoint[] = JSON.parse(savedEndpoints)
        
        // Add all custom models to available models FIRST
        const allCustomModels = endpoints.flatMap(e => e.models || [])
        
        setAvailableModels(prev => ({
          ...prev,
          custom: allCustomModels
        }))
        
        // Then update config
        setConfig(prev => ({ ...prev, custom_endpoints: endpoints }))
      } catch (error) {
        console.error('Error loading custom endpoints:', error)
      }
    }
  }, [])

  // Update available models when custom endpoints change
  useEffect(() => {
    if (config.custom_endpoints) {
      const allCustomModels = config.custom_endpoints.flatMap(e => e.models || [])
      setAvailableModels(prev => ({ ...prev, custom: allCustomModels }))
    }
  }, [config.custom_endpoints])

  // Get model-specific capabilities
  const getModelCapabilities = (modelId: string): ModelCapabilities => {
    // Default capabilities
    const defaults: ModelCapabilities = {
      maxTokens: 4096,
      contextWindow: 128000,
      supportsTemperature: true,
      temperatureRange: [0, 2],
      recommendedTemperature: 0.7
    }

    // Model-specific overrides
    if (modelId.includes('claude-3-opus')) {
      return { ...defaults, maxTokens: 4096, contextWindow: 200000 }
    } else if (modelId.includes('claude-3-5-sonnet')) {
      return { ...defaults, maxTokens: 8192, contextWindow: 200000 }
    } else if (modelId.includes('claude-3-sonnet')) {
      return { ...defaults, maxTokens: 4096, contextWindow: 200000 }
    } else if (modelId.includes('claude-3-haiku')) {
      return { ...defaults, maxTokens: 4096, contextWindow: 200000 }
    } else if (modelId.includes('gpt-4o')) {
      return { ...defaults, maxTokens: 16384, contextWindow: 128000 }
    } else if (modelId.includes('gpt-4-turbo')) {
      return { ...defaults, maxTokens: 4096, contextWindow: 128000 }
    } else if (modelId.includes('gpt-4')) {
      return { ...defaults, maxTokens: 8192, contextWindow: 8192 }
    } else if (modelId.includes('gpt-3.5-turbo')) {
      return { ...defaults, maxTokens: 4096, contextWindow: 16385 }
    } else if (modelId.includes('gemini-pro')) {
      return { ...defaults, maxTokens: 8192, contextWindow: 1000000 }
    } else if (modelId.includes('gemini-1.5')) {
      return { ...defaults, maxTokens: 8192, contextWindow: 2000000 }
    }

    return defaults
  }

  // Get capabilities for currently selected model
  const getActiveModelCapabilities = (role: 'analyst' | 'critic' | 'judge'): ModelCapabilities => {
    const modelId = role === 'analyst' ? config.analyst_model : 
                    role === 'critic' ? config.critic_model : 
                    config.judge_model
    return getModelCapabilities(modelId)
  }

  // Save API keys to encrypted local storage
  const handleSave = () => {
    if (config.anthropic_api_key) {
      localStorage.setItem('encrypted_anthropic_key', encrypt(config.anthropic_api_key))
    }
    if (config.openai_api_key) {
      localStorage.setItem('encrypted_openai_key', encrypt(config.openai_api_key))
    }
    if (config.google_api_key) {
      localStorage.setItem('encrypted_google_key', encrypt(config.google_api_key))
    }
    if (config.ollama_base_url) {
      localStorage.setItem('ollama_base_url', config.ollama_base_url)
    }

    console.log('[DEBUG Frontend] Config being sent:', {
      analyst_model: config.analyst_model,
      custom_endpoints: config.custom_endpoints,
      custom_endpoints_count: config.custom_endpoints?.length || 0,
      has_custom_endpoints: !!config.custom_endpoints
    })

    setIsSaved(true)
    onConfigComplete(config)
    toast.success('Configuration saved!')
    setTimeout(() => setIsSaved(false), 2000)
  }

  // Check if config is valid (at least one provider configured)
  const isConfigValid = 
    config.anthropic_api_key || 
    config.openai_api_key || 
    config.google_api_key || 
    (ollamaConnected && config.ollama_base_url)

  const getModelsForRole = (role: 'analyst' | 'critic' | 'judge') => {
    // Combine all available models
    return [
      ...availableModels.anthropic,
      ...availableModels.openai,
      ...availableModels.google,
      ...availableModels.ollama,
      ...(availableModels.custom || []),
    ]
  }

  const getCostColor = (cost: string) => {
    switch (cost) {
      case 'free': return 'bg-green-100 text-green-700'
      case 'very-low': return 'bg-blue-100 text-blue-700'
      case 'low': return 'bg-cyan-100 text-cyan-700'
      case 'medium': return 'bg-yellow-100 text-yellow-700'
      case 'high': return 'bg-orange-100 text-orange-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  // Load prompts on mount
  useEffect(() => {
    loadDefaultPrompts()
  }, [])

  const tabs = [
    { id: 'models' as const, label: 'Models & API Keys', number: 1, description: 'Select AI models' },
    { id: 'strategy' as const, label: 'Session Strategy', number: 2, description: 'Handle long sessions' },
    { id: 'parameters' as const, label: 'Model Parameters', number: 3, description: 'Fine-tune settings' },
    { id: 'prompts' as const, label: 'Custom Prompts', number: 4, description: 'Customize agents' },
  ]

  return (
    <div className="bg-white rounded-3xl border border-gray-200 p-8">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">LLM Configuration</h2>
        <p className="text-gray-600">
          Configure models, strategies, and parameters for the multi-agent annotation system
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="mb-8">
        <div className="grid grid-cols-4 gap-3">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id
            const isCompleted = tabs.findIndex(t => t.id === activeTab) > tabs.findIndex(t => t.id === tab.id)
            
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`relative p-4 rounded-xl transition-all text-left ${
                  isActive
                    ? 'bg-gradient-to-br from-blue-50 to-purple-50 border-2 border-blue-500 shadow-sm'
                    : isCompleted
                    ? 'bg-gray-50 border-2 border-gray-300 hover:border-gray-400'
                    : 'bg-white border-2 border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold ${
                    isActive
                      ? 'bg-blue-600 text-white'
                      : isCompleted
                      ? 'bg-gray-600 text-white'
                      : 'bg-gray-200 text-gray-600'
                  }`}>
                    {isCompleted ? '✓' : tab.number}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className={`font-semibold text-sm mb-0.5 ${
                      isActive ? 'text-blue-900' : 'text-gray-900'
                    }`}>
                      {tab.label}
                    </div>
                    <div className={`text-xs ${
                      isActive ? 'text-blue-700' : 'text-gray-500'
                    }`}>
                      {tab.description}
                    </div>
                  </div>
                </div>
              </button>
            )
          })}
        </div>
      </div>

      <div className="space-y-8">
        {/* TAB 1: Models & API Keys */}
        {activeTab === 'models' && (
      <div className="space-y-8">
        {/* Agent Model Selection */}
            <div>
              <h3 className="text-lg font-bold text-gray-900 mb-4">Select Models for Each Agent</h3>
              <div className="grid md:grid-cols-3 gap-4">
          {/* Analyst */}
                <div className="group relative bg-gradient-to-br from-purple-50 to-white border-2 border-purple-200 rounded-2xl p-6 hover:border-purple-300 transition-all">
                  <div className="mb-4">
                    <div className="inline-block px-3 py-1 bg-purple-100 text-purple-700 text-xs font-medium rounded-full mb-2">
                      Agent 1
              </div>
                    <h3 className="text-xl font-bold text-gray-900 mb-1">Analyst</h3>
                    <p className="text-sm text-gray-600">Performs initial cognitive analysis</p>
            </div>
            <select
              value={config.analyst_model}
              onChange={(e) => setConfig({ ...config, analyst_model: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 text-sm bg-white"
            >
              {getModelsForRole('analyst').map((model) => (
                <option key={model.id} value={model.id}>
                        {model.name} {model.recommended && '[Recommended]'} - {model.provider}
                </option>
              ))}
            </select>
          </div>

          {/* Critic */}
                <div className="group relative bg-gradient-to-br from-orange-50 to-white border-2 border-orange-200 rounded-2xl p-6 hover:border-orange-300 transition-all">
                  <div className="mb-4">
                    <div className="inline-block px-3 py-1 bg-orange-100 text-orange-700 text-xs font-medium rounded-full mb-2">
                      Agent 2
              </div>
                    <h3 className="text-xl font-bold text-gray-900 mb-1">Critic</h3>
                    <p className="text-sm text-gray-600">Reviews and challenges decisions</p>
            </div>
            <select
              value={config.critic_model}
              onChange={(e) => setConfig({ ...config, critic_model: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-orange-500 text-sm bg-white"
            >
              {getModelsForRole('critic').map((model) => (
                <option key={model.id} value={model.id}>
                        {model.name} {model.recommended && '[Recommended]'} - {model.provider}
                </option>
              ))}
            </select>
          </div>

          {/* Judge */}
                <div className="group relative bg-gradient-to-br from-blue-50 to-white border-2 border-blue-200 rounded-2xl p-6 hover:border-blue-300 transition-all">
                  <div className="mb-4">
                    <div className="inline-block px-3 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded-full mb-2">
                      Agent 3
              </div>
                    <h3 className="text-xl font-bold text-gray-900 mb-1">Judge</h3>
                    <p className="text-sm text-gray-600">Makes final labeling decision</p>
            </div>
            <select
              value={config.judge_model}
              onChange={(e) => setConfig({ ...config, judge_model: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm bg-white"
            >
              {getModelsForRole('judge').map((model) => (
                <option key={model.id} value={model.id}>
                        {model.name} {model.recommended && '[Recommended]'} - {model.provider}
                </option>
              ))}
            </select>
                </div>
          </div>
        </div>

            {/* API Keys Section */}
            <div>
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold text-gray-900">API Keys & Providers</h3>
                  <div className="relative">
                    <button
                      onMouseEnter={() => setShowProviderTooltip(true)}
                      onMouseLeave={() => setShowProviderTooltip(false)}
                      className="text-gray-400 hover:text-gray-600 transition-colors"
                    >
                      <HelpCircle className="w-5 h-5" />
                    </button>
                    {showProviderTooltip && (
                      <div className="absolute left-0 top-8 w-80 bg-gray-900 text-white text-xs rounded-xl p-4 shadow-lg z-10">
                        <div className="space-y-2">
                          <div><strong>Anthropic Claude:</strong> Excellent reasoning, best for Analyst</div>
                          <div><strong>OpenAI GPT:</strong> Versatile and powerful for all roles</div>
                          <div><strong>Google Gemini:</strong> Fast with large context windows</div>
                          <div><strong>Ollama:</strong> Free local models (requires installation)</div>
                        </div>
                        <div className="absolute -top-1 left-4 w-2 h-2 bg-gray-900 transform rotate-45"></div>
                      </div>
                    )}
                  </div>
            </div>
            <button
              onClick={loadAvailableModels}
              disabled={isLoadingModels}
                  className="flex items-center gap-2 px-4 py-2 text-sm border-2 border-gray-200 text-gray-700 rounded-lg hover:border-gray-300 hover:bg-gray-50 transition-all"
            >
              <RefreshCw className={`w-4 h-4 ${isLoadingModels ? 'animate-spin' : ''}`} />
                  Refresh
            </button>
          </div>

              <div className="grid md:grid-cols-2 gap-4">
            {/* Anthropic API Key */}
                <div className="bg-gradient-to-br from-purple-50 to-white border-2 border-purple-100 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-3">
                    <label className="text-sm font-semibold text-gray-900">Anthropic</label>
                    <span className="text-xs text-purple-600 bg-purple-100 px-2 py-1 rounded-full">Claude models</span>
                  </div>
              <div className="relative">
                <input
                  type={showKeys.anthropic ? 'text' : 'password'}
                  value={config.anthropic_api_key || ''}
                  onChange={(e) => setConfig({ ...config, anthropic_api_key: e.target.value })}
                  placeholder="sk-ant-..."
                      className="w-full px-4 py-2.5 pr-10 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 bg-white text-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowKeys({ ...showKeys, anthropic: !showKeys.anthropic })}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                      {showKeys.anthropic ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* OpenAI API Key */}
                <div className="bg-gradient-to-br from-blue-50 to-white border-2 border-blue-100 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-3">
                    <label className="text-sm font-semibold text-gray-900">OpenAI</label>
                    <span className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded-full">GPT models</span>
                  </div>
              <div className="relative">
                <input
                  type={showKeys.openai ? 'text' : 'password'}
                  value={config.openai_api_key || ''}
                  onChange={(e) => setConfig({ ...config, openai_api_key: e.target.value })}
                  placeholder="sk-..."
                      className="w-full px-4 py-2.5 pr-10 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowKeys({ ...showKeys, openai: !showKeys.openai })}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                      {showKeys.openai ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Google API Key */}
                <div className="bg-gradient-to-br from-green-50 to-white border-2 border-green-100 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-3">
                    <label className="text-sm font-semibold text-gray-900">Google</label>
                    <span className="text-xs text-green-600 bg-green-100 px-2 py-1 rounded-full">Gemini models</span>
                  </div>
              <div className="relative">
                <input
                  type={showKeys.google ? 'text' : 'password'}
                  value={config.google_api_key || ''}
                  onChange={(e) => setConfig({ ...config, google_api_key: e.target.value })}
                  placeholder="AIza..."
                      className="w-full px-4 py-2.5 pr-10 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 bg-white text-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowKeys({ ...showKeys, google: !showKeys.google })}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                      {showKeys.google ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Ollama Configuration */}
                <div className="bg-gradient-to-br from-indigo-50 to-white border-2 border-indigo-100 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-3">
                    <label className="text-sm font-semibold text-gray-900">Ollama</label>
                    <span className="text-xs text-indigo-600 bg-indigo-100 px-2 py-1 rounded-full">Local & Free</span>
                  </div>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <input
                    type="text"
                    value={config.ollama_base_url || ''}
                    onChange={(e) => setConfig({ ...config, ollama_base_url: e.target.value })}
                    placeholder="http://localhost:11434"
                        className="w-full px-4 py-2.5 pr-8 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white text-sm"
                  />
                  {ollamaConnected && (
                        <CheckCircle className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-green-600" />
                  )}
                </div>
                <button
                  onClick={testOllamaConnection}
                  disabled={isLoadingModels}
                      className="px-4 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium disabled:opacity-50 text-sm transition-all"
                >
                  Test
                </button>
              </div>
              {ollamaConnected && (
                    <p className="mt-2 text-xs text-green-600 flex items-center gap-1">
                      <CheckCircle className="w-3 h-3" />
                      {availableModels.ollama.length} models available
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Custom Endpoints Section */}
            <div className="mt-8">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-gray-900">Custom Endpoints</h3>
                <button
                  onClick={() => setShowCustomEndpointForm(!showCustomEndpointForm)}
                  className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:from-cyan-600 hover:to-blue-600 transition-all font-medium text-sm"
                >
                  <Server className="w-4 h-4" />
                  Add Custom Endpoint
                </button>
              </div>

              {showCustomEndpointForm && (
                <div className="mb-6 p-6 bg-gradient-to-br from-cyan-50 to-blue-50 border-2 border-cyan-200 rounded-xl">
                  <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <Server className="w-5 h-5 text-cyan-600" />
                    Connect OpenAI-Compatible Endpoint
                  </h4>
                  <p className="text-sm text-gray-600 mb-4">
                    Add your custom LLM endpoint (e.g., LiteLLM, vLLM). We'll automatically discover available models.
                  </p>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Endpoint Name
                      </label>
                      <input
                        type="text"
                        value={newEndpoint.name}
                        onChange={(e) => setNewEndpoint({ ...newEndpoint, name: e.target.value })}
                        placeholder="e.g., Organization"
                        className="w-full px-4 py-2.5 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 bg-white text-sm"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Base URL
                      </label>
                      <input
                        type="text"
                        value={newEndpoint.base_url}
                        onChange={(e) => setNewEndpoint({ ...newEndpoint, base_url: e.target.value })}
                        placeholder="Enter Base URL"
                        className="w-full px-4 py-2.5 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 bg-white text-sm font-mono"
                      />
                      <p className="mt-1 text-xs text-gray-500">Must be OpenAI-compatible (supports /v1/models endpoint)</p>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        API Key (Optional)
                      </label>
                      <input
                        type="password"
                        value={newEndpoint.api_key}
                        onChange={(e) => setNewEndpoint({ ...newEndpoint, api_key: e.target.value })}
                        placeholder="Enter API key if required"
                        className="w-full px-4 py-2.5 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 bg-white text-sm"
                      />
                    </div>
                    
                    <div className="flex gap-3">
                      <button
                        onClick={testCustomEndpoint}
                        disabled={isTestingEndpoint}
                        className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 font-medium disabled:opacity-50 transition-all"
                      >
                        {isTestingEndpoint ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Testing Connection...
                          </>
                        ) : (
                          <>
                  <CheckCircle className="w-4 h-4" />
                            Test & Add Endpoint
                          </>
                        )}
                      </button>
                      <button
                        onClick={() => {
                          setShowCustomEndpointForm(false)
                          setNewEndpoint({ name: '', base_url: '', api_key: '' })
                        }}
                        className="px-4 py-3 border-2 border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 font-medium transition-all"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Connected Endpoints List */}
              {config.custom_endpoints && config.custom_endpoints.length > 0 && (
                <div className="space-y-3">
                  {config.custom_endpoints.map((endpoint) => (
                    <div key={endpoint.id} className="p-4 bg-gradient-to-br from-gray-50 to-white border-2 border-gray-200 rounded-xl">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="font-semibold text-gray-900">{endpoint.name}</h4>
                            {endpoint.connected && (
                              <span className="text-xs text-green-600 bg-green-100 px-2 py-0.5 rounded-full flex items-center gap-1">
                                <CheckCircle className="w-3 h-3" />
                                Connected
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 font-mono mb-2">{endpoint.base_url}</p>
                          <div className="text-xs text-gray-500">
                            <p className="font-medium mb-1">{endpoint.models?.length || 0} models available:</p>
                            {endpoint.models && endpoint.models.length > 0 && (
                              <ul className="list-disc list-inside pl-2 space-y-0.5">
                                {endpoint.models.map((model) => (
                                  <li key={model.id} className="text-gray-600">
                                    <span className="font-mono">{model.id}</span>
                                  </li>
                                ))}
                              </ul>
                            )}
                          </div>
                        </div>
                        <button
                          onClick={() => removeCustomEndpoint(endpoint.id)}
                          className="px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-all"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {(!config.custom_endpoints || config.custom_endpoints.length === 0) && !showCustomEndpointForm && (
                <div className="text-center py-8 px-4 border-2 border-dashed border-gray-200 rounded-xl">
                  <Server className="w-12 h-12 mx-auto text-gray-400 mb-3" />
                  <p className="text-gray-600 mb-2">No custom endpoints configured</p>
                  <p className="text-sm text-gray-500">Add your own OpenAI-compatible endpoint to use custom models</p>
            </div>
              )}
          </div>

            {/* Fallback Configuration */}
            {config.custom_endpoints && config.custom_endpoints.length > 0 && (
              <div className="mt-8 p-6 bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-200 rounded-xl">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                      <AlertCircle className="w-5 h-5 text-amber-600" />
                      Fallback Configuration
                    </h3>
                    <p className="text-sm text-gray-600 mt-1">
                      Automatically switch to commercial models if custom endpoint fails, then retry later
                    </p>
                  </div>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={config.enable_fallback || false}
                      onChange={(e) => setConfig({ ...config, enable_fallback: e.target.checked })}
                      className="w-4 h-4 text-amber-600 border-gray-300 rounded focus:ring-amber-500"
                    />
                    <span className="text-sm font-medium text-gray-900">Enable Fallback</span>
                  </label>
        </div>

                {config.enable_fallback && (
                  <div className="space-y-4 mt-6">
                    <div className="grid md:grid-cols-3 gap-4">
                      {/* Analyst Fallback */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Analyst Fallback
                        </label>
                        <select
                          value={config.fallback_analyst_model}
                          onChange={(e) => setConfig({ ...config, fallback_analyst_model: e.target.value })}
                          className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 text-sm bg-white"
                        >
                          {getModelsForRole('analyst').filter(m => m.provider !== 'custom').map((model) => (
                            <option key={model.id} value={model.id}>
                              {model.name} - {model.provider}
                            </option>
                          ))}
                        </select>
                      </div>

                      {/* Critic Fallback */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Critic Fallback
                        </label>
                        <select
                          value={config.fallback_critic_model}
                          onChange={(e) => setConfig({ ...config, fallback_critic_model: e.target.value })}
                          className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 text-sm bg-white"
                        >
                          {getModelsForRole('critic').filter(m => m.provider !== 'custom').map((model) => (
                            <option key={model.id} value={model.id}>
                              {model.name} - {model.provider}
                            </option>
                          ))}
                        </select>
                      </div>

                      {/* Judge Fallback */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Judge Fallback
                        </label>
                        <select
                          value={config.fallback_judge_model}
                          onChange={(e) => setConfig({ ...config, fallback_judge_model: e.target.value })}
                          className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 text-sm bg-white"
                        >
                          {getModelsForRole('judge').filter(m => m.provider !== 'custom').map((model) => (
                            <option key={model.id} value={model.id}>
                              {model.name} - {model.provider}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    {/* Retry Timer */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Retry Custom Endpoint After (minutes)
                      </label>
                      <input
                        type="number"
                        min="1"
                        max="60"
                        value={config.fallback_retry_after || 5}
                        onChange={(e) => setConfig({ ...config, fallback_retry_after: parseInt(e.target.value) })}
                        className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 text-sm"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        System will attempt to reconnect to custom endpoint after this duration
                      </p>
                    </div>

                    <div className="p-4 bg-amber-100 border border-amber-200 rounded-lg">
                      <p className="text-sm text-amber-900 flex items-start gap-2">
                        <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
                        <span>
                          When a custom endpoint fails, the system will automatically use the fallback model. 
                          After {config.fallback_retry_after || 5} minutes, it will retry the custom endpoint.
                        </span>
                      </p>
                    </div>
                  </div>
              )}
            </div>
            )}
          </div>
        )}

        {/* TAB 2: Session Strategy */}
        {activeTab === 'strategy' && (
          <div className="space-y-8">
            <div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">Session Handling Strategy</h3>
              <p className="text-sm text-gray-600 mb-6">
                Choose how to process sessions with many events. This affects accuracy, cost, and processing time.
              </p>
              
              <div className="grid md:grid-cols-3 gap-4">
            {/* Truncate */}
            <div
              onClick={() => setConfig({ ...config, session_strategy: 'truncate' })}
              className={`p-4 border-2 rounded-xl cursor-pointer transition-all ${
                config.session_strategy === 'truncate'
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <h4 className="font-bold text-gray-900">Truncate</h4>
                {config.session_strategy === 'truncate' && (
                  <CheckCircle className="w-5 h-5 text-blue-600" />
                )}
              </div>
              <p className="text-sm text-gray-600 mb-2">
                Process all events but truncate content based on session size.
              </p>
              <span className="text-xs font-medium text-blue-600 bg-blue-100 px-2 py-1 rounded">
                Recommended
              </span>
        </div>

            {/* Sliding Window */}
            <div
              onClick={() => setConfig({ ...config, session_strategy: 'sliding_window' })}
              className={`p-4 border-2 rounded-xl cursor-pointer transition-all ${
                config.session_strategy === 'sliding_window'
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <h4 className="font-bold text-gray-900">Sliding Window</h4>
                {config.session_strategy === 'sliding_window' && (
                  <CheckCircle className="w-5 h-5 text-blue-600" />
                )}
              </div>
              <p className="text-sm text-gray-600 mb-2">
                Only process last N events. Good for very long sessions.
              </p>
              <span className="text-xs font-medium text-yellow-600 bg-yellow-100 px-2 py-1 rounded">
                For Long Sessions
              </span>
            </div>

            {/* Full */}
            <div
              onClick={() => setConfig({ ...config, session_strategy: 'full' })}
              className={`p-4 border-2 rounded-xl cursor-pointer transition-all ${
                config.session_strategy === 'full'
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <h4 className="font-bold text-gray-900">Full Processing</h4>
                {config.session_strategy === 'full' && (
                  <CheckCircle className="w-5 h-5 text-blue-600" />
                )}
              </div>
              <p className="text-sm text-gray-600 mb-2">
                Process all events with full content. For short sessions only.
              </p>
              <span className="text-xs font-medium text-orange-600 bg-orange-100 px-2 py-1 rounded">
                Under 50 Events
              </span>
            </div>
          </div>

          {/* Window Size (for sliding_window strategy) */}
          {config.session_strategy === 'sliding_window' && (
            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Window Size (number of events to process)
              </label>
              <input
                type="number"
                min="5"
                max="100"
                value={config.window_size}
                onChange={(e) => setConfig({ ...config, window_size: parseInt(e.target.value) })}
                className="w-full md:w-64 px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="mt-1 text-xs text-gray-500">
                Will process the last {config.window_size} events from each session
              </p>
            </div>
          )}
            </div>

            {/* Strategy Comparison */}
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
              <h4 className="font-medium text-gray-900 mb-3">Strategy Comparison</h4>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-300">
                      <th className="text-left py-2 pr-4 font-medium text-gray-700">Strategy</th>
                      <th className="text-left py-2 pr-4 font-medium text-gray-700">Best For</th>
                      <th className="text-left py-2 pr-4 font-medium text-gray-700">Pros</th>
                      <th className="text-left py-2 font-medium text-gray-700">Cons</th>
                    </tr>
                  </thead>
                  <tbody className="text-gray-600">
                    <tr className="border-b border-gray-200">
                      <td className="py-2 pr-4 font-medium">Truncate</td>
                      <td className="py-2 pr-4">Most sessions</td>
                      <td className="py-2 pr-4">Full context, balanced cost</td>
                      <td className="py-2">May lose detail in long content</td>
                    </tr>
                    <tr className="border-b border-gray-200">
                      <td className="py-2 pr-4 font-medium">Sliding Window</td>
                      <td className="py-2 pr-4">100+ events</td>
                      <td className="py-2 pr-4">Consistent time, full recent detail</td>
                      <td className="py-2">Loses early context</td>
                    </tr>
                    <tr>
                      <td className="py-2 pr-4 font-medium">Full</td>
                      <td className="py-2 pr-4">Short sessions</td>
                      <td className="py-2 pr-4">Maximum detail</td>
                      <td className="py-2">Expensive, may fail on long sessions</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: Model Parameters */}
        {activeTab === 'parameters' && (
          <div className="space-y-8">
            <div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">Model Parameters</h3>
              <p className="text-sm text-gray-600 mb-6">
                Configure temperature and token settings. Values are adjusted based on selected models.
              </p>
              {/* Temperature */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Temperature: {config.temperature?.toFixed(1)}
                </label>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={config.temperature}
                  onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>Deterministic (0.0)</span>
                  <span>Balanced (0.7)</span>
                  <span>Creative (2.0)</span>
                </div>
              </div>

              {/* Token Scaling */}
              <div className="grid md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Base Max Tokens
                  </label>
                  <input
                    type="number"
                    min="1024"
                    max="32000"
                    step="1024"
                    value={config.max_tokens_base}
                    onChange={(e) => setConfig({ ...config, max_tokens_base: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Tokens Cap
                  </label>
                  <input
                    type="number"
                    min="4096"
                    max="32000"
                    step="1024"
                    value={config.max_tokens_cap}
                    onChange={(e) => setConfig({ ...config, max_tokens_cap: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tokens Per Event
                  </label>
                  <input
                    type="number"
                    min="50"
                    max="500"
                    step="10"
                    value={config.tokens_per_event}
                    onChange={(e) => setConfig({ ...config, tokens_per_event: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Truncation Limits */}
              {config.session_strategy === 'truncate' && (
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Content Truncation Limits</h4>
                  <div className="grid md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Small (≤20 events)
                      </label>
                      <input
                        type="number"
                        min="50"
                        max="1000"
                        value={config.truncate_content_small}
                        onChange={(e) => setConfig({ ...config, truncate_content_small: parseInt(e.target.value) })}
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Medium (21-50 events)
                      </label>
                      <input
                        type="number"
                        min="50"
                        max="1000"
                        value={config.truncate_content_medium}
                        onChange={(e) => setConfig({ ...config, truncate_content_medium: parseInt(e.target.value) })}
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Large ({'>'}50 events)
                      </label>
                      <input
                        type="number"
                        min="50"
                        max="1000"
                        value={config.truncate_content_large}
                        onChange={(e) => setConfig({ ...config, truncate_content_large: parseInt(e.target.value) })}
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Model-Specific Information */}
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
              <div className="flex gap-2">
                <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-blue-900">
                  <p className="font-medium mb-2">Model Capabilities:</p>
                  <div className="grid md:grid-cols-3 gap-4 text-blue-800">
                    <div>
                      <p className="font-medium">Analyst ({config.analyst_model.split('-')[0]})</p>
                      <p>Max Tokens: {getActiveModelCapabilities('analyst').maxTokens.toLocaleString()}</p>
                      <p>Context: {(getActiveModelCapabilities('analyst').contextWindow / 1000).toFixed(0)}K tokens</p>
                    </div>
                    <div>
                      <p className="font-medium">Critic ({config.critic_model.split('-')[0]})</p>
                      <p>Max Tokens: {getActiveModelCapabilities('critic').maxTokens.toLocaleString()}</p>
                      <p>Context: {(getActiveModelCapabilities('critic').contextWindow / 1000).toFixed(0)}K tokens</p>
                    </div>
                    <div>
                      <p className="font-medium">Judge ({config.judge_model.split('-')[0]})</p>
                      <p>Max Tokens: {getActiveModelCapabilities('judge').maxTokens.toLocaleString()}</p>
                      <p>Context: {(getActiveModelCapabilities('judge').contextWindow / 1000).toFixed(0)}K tokens</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: Custom Prompts */}
        {activeTab === 'prompts' && (
          <div className="space-y-8">
            <div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">Custom Prompts</h3>
              <p className="text-sm text-gray-600 mb-6">
                Customize agent prompts for domain-specific instructions. Current prompts are pre-filled below.
              </p>
              {/* Analyst Prompt */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Analyst Prompt
                </label>
                <textarea
                  rows={8}
                  value={config.analyst_prompt_override || currentPrompts?.analyst || ''}
                  onChange={(e) => setConfig({ ...config, analyst_prompt_override: e.target.value || null })}
                  placeholder="Loading..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent font-mono text-xs"
                />
              </div>

              {/* Critic Prompt */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Critic Prompt
                </label>
                <textarea
                  rows={8}
                  value={config.critic_prompt_override || currentPrompts?.critic || ''}
                  onChange={(e) => setConfig({ ...config, critic_prompt_override: e.target.value || null })}
                  placeholder="Loading..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent font-mono text-xs"
                />
              </div>

              {/* Judge Prompt */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Judge Prompt
                </label>
                <textarea
                  rows={8}
                  value={config.judge_prompt_override || currentPrompts?.judge || ''}
                  onChange={(e) => setConfig({ ...config, judge_prompt_override: e.target.value || null })}
                  placeholder="Loading..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-xs"
                />
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
                <div className="flex gap-2">
                  <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-yellow-800">
                    <p className="font-medium mb-1">Important:</p>
                    <p>Keep the JSON output format and placeholders (LABEL_SCHEMA, events_str, etc.) exactly as shown. Test with a few sessions before running on full dataset.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Navigation & Save */}
        <div className="flex items-center justify-between pt-6 border-t border-gray-200">
          <div className="flex gap-2">
            {activeTab !== 'models' && (
              <button
                onClick={() => {
                  const currentIndex = tabs.findIndex(t => t.id === activeTab)
                  if (currentIndex > 0) {
                    setActiveTab(tabs[currentIndex - 1].id)
                  }
                }}
                className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 font-medium transition-all"
              >
                Previous
              </button>
            )}
            {activeTab !== 'prompts' && (
              <button
                onClick={() => {
                  const currentIndex = tabs.findIndex(t => t.id === activeTab)
                  if (currentIndex < tabs.length - 1) {
                    setActiveTab(tabs[currentIndex + 1].id)
                  }
                }}
                className="px-6 py-3 bg-gray-900 text-white rounded-xl hover:bg-gray-800 font-medium transition-all"
              >
                Next
              </button>
            )}
          </div>
          
          <button
            onClick={handleSave}
            disabled={!isConfigValid}
            className={`px-8 py-3 rounded-xl font-medium flex items-center gap-2 transition-all ${
              isConfigValid
                ? isSaved
                  ? 'bg-green-600 text-white'
                  : 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700 shadow-sm'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
          >
            <Save className="w-5 h-5" />
            {isSaved ? 'Saved Successfully' : 'Save Configuration'}
          </button>
        </div>

        {/* Quick Start Guide - Warning Alert */}
        <div className="mt-6 bg-amber-50 border-2 border-amber-200 rounded-2xl p-5">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-10 h-10 bg-amber-500 rounded-lg flex items-center justify-center">
              <AlertCircle className="w-5 h-5 text-white" />
            </div>
            <div className="flex-1">
              <h4 className="font-bold text-amber-900 mb-3">Quick Start Guide</h4>
              <div className="grid md:grid-cols-2 gap-6 text-sm">
                <div>
                  <p className="font-semibold text-amber-900 mb-2">Recommended Settings:</p>
                  <ul className="space-y-1 text-amber-800">
                    <li className="flex items-start gap-2">
                      <span className="text-amber-500 mt-0.5">•</span>
                      <span>Strategy: Truncate</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-amber-500 mt-0.5">•</span>
                      <span>Temperature: 0.5 - 0.8</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-amber-500 mt-0.5">•</span>
                      <span>Test with 5-10 sessions first</span>
                    </li>
          </ul>
                </div>
                <div>
                  <p className="font-semibold text-amber-900 mb-2">For Long Sessions (100+ events):</p>
                  <ul className="space-y-1 text-amber-800">
                    <li className="flex items-start gap-2">
                      <span className="text-amber-500 mt-0.5">•</span>
                      <span>Strategy: Sliding Window</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-amber-500 mt-0.5">•</span>
                      <span>Window Size: 30-50 events</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-amber-500 mt-0.5">•</span>
                      <span>Monitor flagged sessions</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
