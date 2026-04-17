export interface UserOut {
  id: string
  github_id: number
  github_login: string
  name: string | null
  email: string | null
  avatar_url: string | null
  created_at: string
}

export interface RunOut {
  id: string
  job_id: string
  dataset_id: string
  dataset_filename: string
  total_sessions: number
  completed_sessions: number
  status: 'running' | 'paused' | 'completed' | 'failed'
  llm_config_snapshot: Record<string, unknown>
  flagged_count: number
  resolved_count: number
  error_message: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
}

export interface RunListOut {
  items: RunOut[]
  total: number
}

export interface PresetOut {
  id: string
  name: string
  description: string | null
  config_json: Record<string, unknown>
  created_at: string
  updated_at: string
}
