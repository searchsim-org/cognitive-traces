/**
 * API client for communicating with the Cognitive Traces backend
 */

import axios, { AxiosInstance } from 'axios'
import { getBackendToken, clearBackendTokenCache } from '@/lib/auth-client'
import type { UserOut, RunListOut, RunOut, PresetOut } from '@/types/auth'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 10000, // 10 seconds (faster timeout for status checks)
    })

    // Request interceptor — attach backend-bound JWT when a NextAuth session is present.
    this.client.interceptors.request.use(
      async (config) => {
        try {
          const token = await getBackendToken()
          if (token) {
            config.headers = config.headers ?? {}
            ;(config.headers as any).Authorization = `Bearer ${token}`
          }
        } catch {
          // Network blip fetching the backend token — proceed unauthenticated
          // rather than blocking the request. Backend will 401 if auth was required.
        }
        return config
      },
      (error) => Promise.reject(error),
    )

    // Response interceptor — clear the backend-token cache on 401 so the next
    // request tries to mint a fresh one. No redirect: anonymous users hitting
    // an authed endpoint should just get their 401 back; the caller decides
    // how to react.
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          clearBackendTokenCache()
        }
        return Promise.reject(error)
      },
    )
  }

  // Annotation endpoints
  async annotateSession(data: any) {
    return this.client.post('/annotations/annotate', data)
  }

  async batchAnnotate(data: any) {
    return this.client.post('/annotations/batch-annotate', data)
  }

  async uploadDataset(file: File, datasetType: string) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('dataset_type', datasetType)
    
    return this.client.post('/annotations/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  }

  async getDatasetInfo(datasetId: string, page: number = 1, limit: number = 10) {
    return this.client.get(`/annotations/dataset/${datasetId}`, {
      params: { page, limit }
    })
  }

  async getJobStatus(jobId: string) {
    return this.client.get(`/annotations/job/${jobId}`)
  }

  async startAnnotationJob(datasetId: string, llmConfig: any, datasetName: string = 'dataset') {
    console.log('[API] Starting annotation job with config:', {
      analyst_model: llmConfig.analyst_model,
      critic_model: llmConfig.critic_model,
      judge_model: llmConfig.judge_model,
      has_anthropic_key: !!llmConfig.anthropic_api_key,
      has_openai_key: !!llmConfig.openai_api_key,
      has_google_key: !!llmConfig.google_api_key,
      has_mistral_key: !!llmConfig.mistral_api_key,
      mistral_key_length: llmConfig.mistral_api_key?.length || 0,
      mistral_key_preview: llmConfig.mistral_api_key ? `***${llmConfig.mistral_api_key.substring(0, 8)}` : 'NOT SET',
    })
    return this.client.post('/annotations/start-job', {
      dataset_id: datasetId,
      llm_config: llmConfig,
      dataset_name: datasetName,
    })
  }

  async getSessionLog(jobId: string, sessionId: string) {
    return this.client.get(`/annotations/job/${jobId}/session/${sessionId}/log`)
  }

  async stopJob(jobId: string) {
    return this.client.post(`/annotations/job/${jobId}/stop`)
  }

  async resumeJob(jobId: string, datasetId?: string, llmConfig?: any) {
    return this.client.post(`/annotations/job/${jobId}/resume`, {
      dataset_id: datasetId,
      llm_config: llmConfig
    })
  }

  async getDefaultConfig() {
    return this.client.get('/annotations/config/default')
  }

  async getDefaultPrompts() {
    return this.client.get('/annotations/config/prompts')
  }

  async resolveSession(jobId: string, sessionId: string, label: string, note: string, datasetName: string) {
    return this.client.post(`/annotations/job/${jobId}/session/${sessionId}/resolve`, {
      label,
      note,
      dataset_name: datasetName
    })
  }

  // Generic GET method
  async get(path: string, config?: any) {
    return this.client.get(path, config)
  }

  // Generic POST method
  async post(path: string, data?: any, config?: any) {
    return this.client.post(path, data, config)
  }

  // Session endpoints
  async listSessions(params?: { skip?: number; limit?: number; dataset?: string }) {
    return this.client.get('/sessions', { params })
  }

  async getSession(sessionId: string) {
    return this.client.get(`/sessions/${sessionId}`)
  }

  async deleteSession(sessionId: string) {
    return this.client.delete(`/sessions/${sessionId}`)
  }

  // Model endpoints
  async getModelInfo() {
    return this.client.get('/models/info')
  }

  async getAvailableModels(params?: {
    anthropic_key?: string
    openai_key?: string
    google_key?: string
    mistral_key?: string
    ollama_url?: string
    include_ollama?: boolean
  }) {
    return this.client.get('/models/available', { params })
  }

  async getAnthropicModels(apiKey?: string) {
    return this.client.get('/models/anthropic', { params: { api_key: apiKey } })
  }

  async getOpenAIModels(apiKey?: string) {
    return this.client.get('/models/openai', { params: { api_key: apiKey } })
  }

  async getGoogleModels(apiKey?: string) {
    return this.client.get('/models/google', { params: { api_key: apiKey } })
  }

  async getMistralModels(apiKey?: string) {
    return this.client.get('/models/mistral', { params: { api_key: apiKey } })
  }

  async getOllamaModels(baseUrl?: string) {
    return this.client.get('/models/ollama', { params: { base_url: baseUrl } })
  }

  async predictLabels(data: any) {
    return this.client.post('/models/predict', data)
  }

  // Export endpoints
  async exportCsv(params?: { dataset?: string; session_ids?: string }) {
    return this.client.get('/export/csv', {
      params,
      responseType: 'blob',
    })
  }

  async exportJson(params?: { dataset?: string; session_ids?: string }) {
    return this.client.get('/export/json', {
      params,
      responseType: 'blob',
    })
  }

  // Health check
  async healthCheck() {
    return this.client.get('/health')
  }

  // Auth / users
  async getMe() {
    return this.client.get<UserOut>('/users/me')
  }

  // Runs
  async listRuns(limit = 50, offset = 0) {
    return this.client.get<RunListOut>('/runs', { params: { limit, offset } })
  }
  async getRun(id: string) {
    return this.client.get<RunOut>(`/runs/${id}`)
  }
  async deleteRun(id: string) {
    return this.client.delete(`/runs/${id}`)
  }

  // Config presets
  async listPresets() {
    return this.client.get<PresetOut[]>('/configs')
  }
  async createPreset(body: { name: string; description?: string; config_json: Record<string, unknown> }) {
    return this.client.post<PresetOut>('/configs', body)
  }
  async updatePreset(id: string, body: { name?: string; description?: string; config_json?: Record<string, unknown> }) {
    return this.client.patch<PresetOut>(`/configs/${id}`, body)
  }
  async deletePreset(id: string) {
    return this.client.delete(`/configs/${id}`)
  }
}

export const api = new ApiClient()
export default api

