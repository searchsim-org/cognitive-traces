'use client'

import { useState, useEffect } from 'react'
import { Eye, EyeOff, Save, Key, Brain, RefreshCw, Server, CheckCircle, XCircle } from 'lucide-react'
import CryptoJS from 'crypto-js'
import { api } from '@/lib/api'
import toast from 'react-hot-toast'

interface LLMConfigPanelProps {
  onConfigComplete: (config: LLMConfig) => void
}

interface LLMConfig {
  analyst_model: string
  critic_model: string
  judge_model: string
  anthropic_api_key?: string
  openai_api_key?: string
  google_api_key?: string
  ollama_base_url?: string
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

// Simple encryption key (in production, use a more secure method)
const ENCRYPTION_KEY = 'cognitive-traces-key-v1'

export function LLMConfigPanel({ onConfigComplete }: LLMConfigPanelProps) {
  const [config, setConfig] = useState<LLMConfig>({
    analyst_model: 'claude-3-5-sonnet-20241022',
    critic_model: 'gpt-4o',
    judge_model: 'gpt-4o',
    anthropic_api_key: '',
    openai_api_key: '',
    google_api_key: '',
    ollama_base_url: 'http://localhost:11434',
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
  }>({
    anthropic: [],
    openai: [],
    google: [],
    ollama: [],
  })

  const [isLoadingModels, setIsLoadingModels] = useState(false)
  const [ollamaConnected, setOllamaConnected] = useState(false)
  const [isSaved, setIsSaved] = useState(false)

  // Encryption/Decryption functions
  const encrypt = (text: string): string => {
    return CryptoJS.AES.encrypt(text, ENCRYPTION_KEY).toString()
  }

  const decrypt = (ciphertext: string): string => {
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
      setAvailableModels(models)
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

  return (
    <div className="bg-white rounded-3xl border border-gray-200 p-8">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">LLM Configuration</h2>
        <p className="text-gray-600">
          Configure AI models for each agent. Choose from Anthropic, OpenAI, Google, or local Ollama models.
        </p>
      </div>

      <div className="space-y-8">
        {/* Agent Model Selection */}
        <div className="grid md:grid-cols-3 gap-6">
          {/* Analyst */}
          <div className="p-6 border border-gray-200 rounded-2xl">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-10 h-10 rounded-xl bg-purple-100 flex items-center justify-center">
                <Brain className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <h3 className="font-bold text-gray-900">Analyst</h3>
                <p className="text-xs text-gray-500">Initial analysis</p>
              </div>
            </div>
            <select
              value={config.analyst_model}
              onChange={(e) => setConfig({ ...config, analyst_model: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
            >
              {getModelsForRole('analyst').map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name} {model.recommended && '⭐'} ({model.provider})
                </option>
              ))}
            </select>
          </div>

          {/* Critic */}
          <div className="p-6 border border-gray-200 rounded-2xl">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-10 h-10 rounded-xl bg-orange-100 flex items-center justify-center">
                <Brain className="w-5 h-5 text-orange-600" />
              </div>
              <div>
                <h3 className="font-bold text-gray-900">Critic</h3>
                <p className="text-xs text-gray-500">Review & challenge</p>
              </div>
            </div>
            <select
              value={config.critic_model}
              onChange={(e) => setConfig({ ...config, critic_model: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent text-sm"
            >
              {getModelsForRole('critic').map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name} {model.recommended && '⭐'} ({model.provider})
                </option>
              ))}
            </select>
          </div>

          {/* Judge */}
          <div className="p-6 border border-gray-200 rounded-2xl">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center">
                <Brain className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h3 className="font-bold text-gray-900">Judge</h3>
                <p className="text-xs text-gray-500">Final decision</p>
              </div>
            </div>
            <select
              value={config.judge_model}
              onChange={(e) => setConfig({ ...config, judge_model: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            >
              {getModelsForRole('judge').map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name} {model.recommended && '⭐'} ({model.provider})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* API Keys */}
        <div className="border-t border-gray-200 pt-8">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <Key className="w-5 h-5 text-gray-600" />
              <h3 className="text-lg font-bold text-gray-900">API Keys & Configuration</h3>
            </div>
            <button
              onClick={loadAvailableModels}
              disabled={isLoadingModels}
              className="flex items-center gap-2 px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              <RefreshCw className={`w-4 h-4 ${isLoadingModels ? 'animate-spin' : ''}`} />
              Refresh Models
            </button>
          </div>

          <div className="space-y-4">
            {/* Anthropic API Key */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Anthropic API Key <span className="text-gray-500">(for Claude models)</span>
              </label>
              <div className="relative">
                <input
                  type={showKeys.anthropic ? 'text' : 'password'}
                  value={config.anthropic_api_key || ''}
                  onChange={(e) => setConfig({ ...config, anthropic_api_key: e.target.value })}
                  placeholder="sk-ant-..."
                  className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                <button
                  type="button"
                  onClick={() => setShowKeys({ ...showKeys, anthropic: !showKeys.anthropic })}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showKeys.anthropic ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {/* OpenAI API Key */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                OpenAI API Key <span className="text-gray-500">(for GPT models)</span>
              </label>
              <div className="relative">
                <input
                  type={showKeys.openai ? 'text' : 'password'}
                  value={config.openai_api_key || ''}
                  onChange={(e) => setConfig({ ...config, openai_api_key: e.target.value })}
                  placeholder="sk-..."
                  className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <button
                  type="button"
                  onClick={() => setShowKeys({ ...showKeys, openai: !showKeys.openai })}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showKeys.openai ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {/* Google API Key */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Google API Key <span className="text-gray-500">(for Gemini models)</span>
              </label>
              <div className="relative">
                <input
                  type={showKeys.google ? 'text' : 'password'}
                  value={config.google_api_key || ''}
                  onChange={(e) => setConfig({ ...config, google_api_key: e.target.value })}
                  placeholder="AIza..."
                  className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
                <button
                  type="button"
                  onClick={() => setShowKeys({ ...showKeys, google: !showKeys.google })}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showKeys.google ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {/* Ollama Configuration */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Ollama Base URL <span className="text-gray-500">(for local models - FREE)</span>
              </label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Server className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    value={config.ollama_base_url || ''}
                    onChange={(e) => setConfig({ ...config, ollama_base_url: e.target.value })}
                    placeholder="http://localhost:11434"
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                  {ollamaConnected && (
                    <CheckCircle className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-green-600" />
                  )}
                </div>
                <button
                  onClick={testOllamaConnection}
                  disabled={isLoadingModels}
                  className="px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 font-medium disabled:opacity-50"
                >
                  Test
                </button>
              </div>
              {ollamaConnected && (
                <p className="mt-2 text-sm text-green-600 flex items-center gap-1">
                  <CheckCircle className="w-4 h-4" />
                  Connected • {availableModels.ollama.length} models available
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end pt-6">
          <button
            onClick={handleSave}
            disabled={!isConfigValid}
            className={`px-8 py-3 rounded-xl font-medium flex items-center gap-2 transition-all ${
              isConfigValid
                ? isSaved
                  ? 'bg-green-600 text-white'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
          >
            <Save className="w-5 h-5" />
            {isSaved ? 'Configuration Saved!' : 'Save Configuration'}
          </button>
        </div>

        {/* Info Box */}
        <div className="bg-gray-50 rounded-xl p-4 text-sm text-gray-600">
          <p className="font-medium text-gray-900 mb-2">💡 Provider Options:</p>
          <ul className="space-y-1">
            <li>• <strong>Anthropic Claude:</strong> Best for complex reasoning (Analyst)</li>
            <li>• <strong>OpenAI GPT:</strong> Versatile, great all-rounder (Critic, Judge)</li>
            <li>• <strong>Google Gemini:</strong> Fast with massive context windows</li>
            <li>• <strong>Ollama:</strong> Run models locally, completely free and private</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
