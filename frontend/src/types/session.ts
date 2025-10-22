/**
 * TypeScript types for sessions
 */

import { AnnotatedEvent } from './annotation'

export interface Session {
  id: string
  session_id: string
  dataset: string
  user_id?: string
  start_time: string
  end_time: string
  num_events: number
  has_annotations: boolean
}

export interface SessionDetail extends Session {
  annotated_events: AnnotatedEvent[]
}

export interface SessionListResponse {
  sessions: Session[]
  total: number
  skip: number
  limit: number
}

export interface SessionStatistics {
  total_sessions: number
  total_events: number
  avg_events_per_session: number
  label_distribution: Record<string, number>
  dataset_breakdown: Record<string, number>
}

