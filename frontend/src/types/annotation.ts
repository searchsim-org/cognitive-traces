/**
 * TypeScript types for cognitive annotations
 */

export enum CognitiveLabel {
  FollowingScent = 'FollowingScent',
  ApproachingSource = 'ApproachingSource',
  DietEnrichment = 'DietEnrichment',
  PoorScent = 'PoorScent',
  LeavingPatch = 'LeavingPatch',
  ForagingSuccess = 'ForagingSuccess',
}

export interface EventData {
  event_id: string
  timestamp: string
  action_type: 'QUERY' | 'CLICK' | 'RATE' | 'VIEW' | string
  content: string
  metadata?: Record<string, any>
}

export interface AgentDecision {
  agent_name: 'analyst' | 'critic' | 'judge'
  label: CognitiveLabel
  justification: string
  confidence?: number
}

export interface AnnotatedEvent {
  event_id: string
  cognitive_label: CognitiveLabel
  agent_decisions: AgentDecision[]
  final_justification: string
  confidence_score: number
}

export interface AnnotationRequest {
  session_id: string
  events: EventData[]
  dataset_type?: 'aol' | 'stackoverflow' | 'movielens' | 'custom'
  use_full_pipeline?: boolean
}

export interface AnnotationResponse {
  session_id: string
  annotated_events: AnnotatedEvent[]
  processing_time: number
  flagged_for_review: boolean
}

export interface BatchAnnotationRequest {
  sessions: AnnotationRequest[]
  priority?: number
}

export interface JobStatus {
  job_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  completed: number
  total: number
  error?: string
}

