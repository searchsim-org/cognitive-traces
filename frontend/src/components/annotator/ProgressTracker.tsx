'use client'

import { useState, useEffect } from 'react'
import { CheckCircle2, XCircle, Loader2, FileText, AlertTriangle, Eye, X } from 'lucide-react'
import { api } from '@/lib/api'
import toast from 'react-hot-toast'

interface ProgressTrackerProps {
  jobId: string
  totalSessions: number
  sessionIds: string[]
  onComplete: () => void
  onStopped?: () => void
}

interface SessionStatus {
  session_id: string
  status: 'pending' | 'processing' | 'completed' | 'error' | 'flagged'
  progress?: number
}

export function ProgressTracker({ jobId, totalSessions, sessionIds: propSessionIds, onComplete, onStopped }: ProgressTrackerProps) {
  const [jobStatus, setJobStatus] = useState<any>(null)
  const [sessionLogs, setSessionLogs] = useState<Map<string, any>>(new Map())
  const [selectedLog, setSelectedLog] = useState<any | null>(null)
  const [showLogModal, setShowLogModal] = useState(false)
  const [isPolling, setIsPolling] = useState(true)
  const [isStopRequested, setIsStopRequested] = useState(false)
  const [showStopConfirm, setShowStopConfirm] = useState(false)
  const [dismissedErrors, setDismissedErrors] = useState(false)
  
  // Use session IDs from job status if available, otherwise use prop
  const sessionIds = jobStatus?.session_ids || propSessionIds

  // Poll for job status
  useEffect(() => {
    if (!isPolling) return

    const fetchStatus = async () => {
      try {
        const response = await api.getJobStatus(jobId)
        const status = response.data
        
        console.log('[ProgressTracker] Status:', status.status, `${status.completed_sessions}/${status.total_sessions}`, `Sessions: ${status.session_ids?.length || 0}`)
        setJobStatus(status)

        // Stop polling if completed, stopped, or failed
        if (status.status === 'completed' || status.status === 'stopped' || status.status === 'failed') {
          setIsPolling(false)
          
          if (status.status === 'completed') {
            const hasFlaggedSessions = status.flagged_sessions && status.flagged_sessions.length > 0
            if (hasFlaggedSessions) {
              toast.success('All sessions annotated successfully! Review flagged sessions.')
            } else {
              toast.success('All sessions annotated successfully! No sessions flagged for review.')
            }
            setTimeout(() => onComplete(), 2000)
          } else if (status.status === 'stopped') {
            toast.success('Job stopped successfully. Progress saved via checkpoint.')
            if (onStopped) {
              setTimeout(() => onStopped(), 2000)
            }
          }
        }
      } catch (error: any) {
        // Handle timeout gracefully - the backend is busy processing LLM requests
        if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
          console.log('[ProgressTracker] Status check timed out (backend busy), will retry...')
          // Don't show error to user, just keep polling
        } else {
          console.error('[ProgressTracker] Error fetching status:', error)
          // Only show error toast for non-timeout errors
          if (!error.message?.includes('timeout')) {
            toast.error('Failed to fetch job status')
          }
        }
      }
    }
    
    // Poll immediately on mount
    fetchStatus()

    const pollInterval = setInterval(fetchStatus, 2000) // Poll every 2 seconds

    return () => clearInterval(pollInterval)
  }, [jobId, isPolling, onComplete, onStopped])

  // Stop job
  const handleStopJob = async () => {
    setIsStopRequested(true)
    toast.loading('Requesting stop...', { id: 'stop' })

    try {
      await api.stopJob(jobId)
      toast.success('Stop requested. Job will finish current session and stop.', { id: 'stop' })
    } catch (error: any) {
      toast.error('Failed to stop job', { id: 'stop' })
      setIsStopRequested(false)
    }
  }

  // Load session log
  const loadSessionLog = async (sessionId: string) => {
    if (sessionLogs.has(sessionId)) {
      setSelectedLog(sessionLogs.get(sessionId))
      setShowLogModal(true)
      return
    }

    try {
      const response = await api.getSessionLog(jobId, sessionId)
      const log = response.data
      
      setSessionLogs(new Map(sessionLogs.set(sessionId, log)))
      setSelectedLog(log)
      setShowLogModal(true)
    } catch (error: any) {
      if (error.response?.status !== 404) {
        toast.error('Failed to load session log')
      }
    }
  }

  const progressPercentage = jobStatus?.progress_percentage || 0
  const completedSessions = jobStatus?.completed_sessions || 0
  const eventCounts: Record<string, number> = jobStatus?.session_event_counts || {}
  const isTerminal = jobStatus ? (
    jobStatus.status === 'completed' ||
    jobStatus.status === 'stopped' ||
    jobStatus.status === 'failed' ||
    jobStatus.status === 'idle'
  ) : false

  return (
    <div className="space-y-6">
      {/* Progress Overview */}
      <div className="bg-white rounded-3xl border border-gray-200 p-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Annotation Progress</h2>
            <p className="text-gray-600">
              Processing {totalSessions} sessions with multi-agent framework
            </p>
          </div>
          {!isTerminal && !isStopRequested && (
            <button
              onClick={() => setShowStopConfirm(true)}
              className="px-6 py-3 bg-red-600 text-white rounded-xl hover:bg-red-700 font-medium flex items-center gap-2 transition-colors"
            >
              <XCircle className="w-5 h-5" />
              Stop Job
            </button>
          )}
          {isStopRequested && (
            <div className="px-6 py-3 bg-orange-100 text-orange-800 rounded-xl font-medium flex items-center gap-2">
              <Loader2 className="w-5 h-5 animate-spin" />
              Stopping...
            </div>
          )}
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-gray-700">
              {completedSessions} / {totalSessions} sessions completed
            </span>
            <span className="text-sm font-bold text-blue-600">
              {progressPercentage.toFixed(1)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
            <div
              className="h-full bg-blue-600 transition-all duration-500 ease-out flex items-center justify-end pr-2"
              style={{ width: `${progressPercentage}%` }}
            >
              {progressPercentage > 10 && (
                <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
              )}
            </div>
          </div>
          {/* {jobStatus?.disagreement_model && (
            <div className="mt-2 text-xs">
              {jobStatus.disagreement_model.loaded ? (
                <span className="text-green-600">Disagreement model: loaded</span>
              ) : (
                <span className="text-red-600">Disagreement model: not loaded{jobStatus.disagreement_model.error ? ` — ${jobStatus.disagreement_model.error}` : ''}</span>
              )}
            </div>
          )} */}
        </div>

        {/* Current Session */}
        {jobStatus?.current_session && !isStopRequested && (
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-blue-600 animate-spin flex-shrink-0" />
            <div>
              <div className="font-medium text-blue-900">
                Currently processing: {jobStatus.current_session}
              </div>
              <div className="text-sm text-blue-700">
                Analyst → Critic → Judge pipeline
              </div>
            </div>
          </div>
        )}

        {/* Stopped Status */}
        {jobStatus?.status === 'stopped' && (
          <div className="bg-orange-50 border border-orange-200 rounded-xl p-4 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-orange-600 flex-shrink-0" />
            <div>
              <div className="font-medium text-orange-900">
                Job Stopped
              </div>
              <div className="text-sm text-orange-700">
                Progress has been saved. You can resume this job later by uploading the same dataset with the same name.
              </div>
            </div>
          </div>
        )}

        {/* Statistics Grid */}
        <div className="grid grid-cols-3 gap-4 mt-6">
          <div className="bg-gray-50 rounded-xl p-4 text-center">
            <div className="text-3xl font-bold text-gray-900">{completedSessions}</div>
            <div className="text-sm text-gray-600 mt-1">Completed</div>
          </div>
          <div className="bg-gray-50 rounded-xl p-4 text-center">
            <div className="text-3xl font-bold text-blue-600">
              {totalSessions - completedSessions}
            </div>
            <div className="text-sm text-gray-600 mt-1">Remaining</div>
          </div>
          <div className="bg-gray-50 rounded-xl p-4 text-center">
            <div className="text-3xl font-bold text-orange-600">
              {jobStatus?.errors?.length || 0}
            </div>
            <div className="text-sm text-gray-600 mt-1">Errors</div>
          </div>
        </div>
      </div>

      {/* Session List with Logs */}
      <div className="bg-white rounded-3xl border border-gray-200 p-8">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-bold text-gray-900">Session Details</h3>
          <span className="text-sm text-gray-500">Click to view agent logs</span>
        </div>

        <div className="space-y-2 max-h-[400px] overflow-y-auto">
          {/* Render session items using actual session IDs */}
          {sessionIds.length === 0 ? (
            <div className="flex items-center justify-center py-8 text-gray-500">
              <Loader2 className="w-5 h-5 animate-spin mr-2" />
              Loading session list...
            </div>
          ) : (
            sessionIds.map((sessionId: any, i: any) => {
            const sessionNum = i + 1
            const isCompleted = sessionNum <= completedSessions
            const isCurrent = jobStatus?.current_session === sessionId
            const isPending = sessionNum > completedSessions + 1

            return (
              <div
                key={sessionId}
                className={`flex items-center justify-between p-4 rounded-xl border transition-all ${
                  isCompleted
                    ? 'bg-green-50 border-green-200'
                    : isCurrent
                    ? 'bg-blue-50 border-blue-300 animate-pulse'
                    : 'bg-gray-50 border-gray-200'
                }`}
              >
                <div className="flex items-center gap-3">
                  {isCompleted ? (
                    <CheckCircle2 className="w-5 h-5 text-green-600" />
                  ) : isCurrent ? (
                    <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                  ) : (
                    <div className="w-5 h-5 rounded-full border-2 border-gray-300" />
                  )}
                  <div>
                    <div className="font-medium text-gray-900">
                      {sessionId}
                      <span className="ml-2 text-xs text-gray-500">({eventCounts[sessionId] || 0} events)</span>
                      {isCurrent && (
                        <span className="ml-2 text-xs text-blue-600">(processing)</span>
                      )}
                    </div>
                    <div className="text-xs text-gray-500">
                      {isCompleted
                        ? 'Annotation complete'
                        : isCurrent
                        ? 'In progress...'
                        : 'Waiting'}
                    </div>
                  </div>
                </div>

                {isCompleted && (
                  <button
                    onClick={() => loadSessionLog(sessionId)}
                    className="flex items-center gap-2 px-4 py-2 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <Eye className="w-4 h-4" />
                    View Logs
                  </button>
                )}
              </div>
            )
          }))}
        </div>

        {/* Errors */}
        {jobStatus?.errors && jobStatus.errors.length > 0 && !dismissedErrors && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-xl relative">
            <button
              onClick={() => setDismissedErrors(true)}
              className="absolute top-2 right-2 text-red-400 hover:text-red-600 transition-colors p-1 rounded-lg hover:bg-red-100"
              title="Dismiss errors"
            >
              <X className="w-4 h-4" />
            </button>
            <div className="flex items-center gap-2 text-red-800 font-medium mb-2">
              <AlertTriangle className="w-5 h-5" />
              Errors Encountered
            </div>
            <ul className="text-sm text-red-700 space-y-1 pr-8">
              {jobStatus.errors.map((error: string, i: number) => (
                <li key={i}>• {error}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Log Modal */}
      {showLogModal && selectedLog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-2xl font-bold text-gray-900">
                  Session Logs: {selectedLog.session_id}
                </h3>
                <button
                  onClick={() => setShowLogModal(false)}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  ×
                </button>
              </div>
              {selectedLog.flagged_for_review && (
                <div className="mt-4 flex items-center gap-2 px-4 py-2 bg-orange-100 text-orange-800 rounded-lg">
                  <AlertTriangle className="w-5 h-5" />
                  <span className="font-medium">
                    Flagged for human review (Disagreement score: {selectedLog.max_disagreement?.toFixed(2)})
                  </span>
                </div>
              )}
            </div>

            <div className="p-6 overflow-y-auto flex-1">
              {/* Agent Interactions */}
              <div className="space-y-6">
                {selectedLog.agent_interactions?.map((interaction: any, i: number) => (
                  <div key={i} className="border border-gray-200 rounded-xl p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                          interaction.agent === 'analyst'
                            ? 'bg-purple-100'
                            : interaction.agent === 'critic'
                            ? 'bg-orange-100'
                            : 'bg-blue-100'
                        }`}>
                          <span className="text-lg">
                            {interaction.agent === 'analyst' ? '🔍' : interaction.agent === 'critic' ? '🧐' : '⚖️'}
                          </span>
                        </div>
                        <div>
                          <div className="font-bold text-gray-900 capitalize">
                            {interaction.agent}
                          </div>
                          <div className="text-sm text-gray-500">
                            Step {interaction.step} • {interaction.elapsed_time?.toFixed(2)}s
                          </div>
                        </div>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                        interaction.status === 'completed'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}>
                        {interaction.status}
                      </span>
                    </div>

                    {interaction.decisions && (
                      <div className="mt-3 space-y-2">
                        {interaction.decisions.slice(0, 3).map((decision: any, j: number) => (
                          <div key={j} className="bg-gray-50 rounded-lg p-3 text-sm">
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-medium text-gray-900">
                                {decision.label || decision.final_label}
                              </span>
                              <span className="text-xs text-gray-500">
                                Confidence: {(decision.confidence * 100).toFixed(0)}%
                              </span>
                            </div>
                            <p className="text-gray-600 text-xs line-clamp-2">
                              {decision.justification}
                            </p>
                          </div>
                        ))}
                        {interaction.decisions.length > 3 && (
                          <div className="text-xs text-gray-500 text-center">
                            +{interaction.decisions.length - 3} more events
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Final Events */}
              {selectedLog.events && selectedLog.events.length > 0 && (
                <div className="mt-6">
                  <h4 className="font-bold text-gray-900 mb-3">Final Cognitive Traces</h4>
                  <div className="space-y-2">
                    {selectedLog.events.map((event: any, i: number) => (
                      <div key={i} className="bg-gray-50 rounded-lg p-3 text-sm">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-bold text-gray-900">
                            {event.cognitive_label}
                          </span>
                          {event.flagged_for_review && (
                            <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded text-xs font-medium">
                              Flagged
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-gray-600">
                          <strong>Event:</strong> {event.action_type}
                        </div>
                        <div className="text-xs text-gray-500 mt-1 line-clamp-2">
                          {event.judge_justification}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Stop Confirmation Modal */}
      {showStopConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-md overflow-hidden">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-xl font-bold text-gray-900">Stop Annotation?</h3>
              <p className="mt-2 text-sm text-gray-600">
                Are you sure you want to stop the annotation job? Progress will be saved and you can resume later.
              </p>
            </div>
            <div className="p-6 flex items-center justify-end gap-3">
              <button
                onClick={() => setShowStopConfirm(false)}
                className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  setShowStopConfirm(false)
                  await handleStopJob()
                }}
                className="px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700"
              >
                Stop Job
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

