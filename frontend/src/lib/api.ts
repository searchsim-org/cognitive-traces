/**
 * API client for communicating with the Cognitive Traces backend
 */

import axios, { AxiosInstance } from 'axios'

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

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('auth_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized
          localStorage.removeItem('auth_token')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
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
}

export const api = new ApiClient()
export default api

