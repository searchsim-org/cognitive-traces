'use client'

import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import toast from 'react-hot-toast'

const LABELS: { value: string; title: string; desc: string }[] = [
  { value: 'FollowingScent', title: 'Following a strong scent', desc: 'Targeted query indicating strong information scent.' },
  { value: 'ApproachingSource', title: 'Approaching an information source', desc: 'Clicking a promising result to investigate further.' },
  { value: 'DietEnrichment', title: 'Enriching the information diet', desc: 'Refining the query to broaden or narrow the scope.' },
  { value: 'PoorScent', title: 'Poor scent in the current patch', desc: 'Issuing a new query without clicks from the current SERP.' },
  { value: 'LeavingPatch', title: 'Deciding to leave the patch', desc: "Ending a session after multiple reformulations without success." },
  { value: 'ForagingSuccess', title: 'Successful foraging within the patch', desc: 'Finding an answer directly on the SERP without clicks.' }
]

interface FlaggedSessionsProps {
  jobId: string
  datasetName: string
  onFinish?: () => void
}

export function FlaggedSessions({ jobId, datasetName, onFinish }: FlaggedSessionsProps) {
  const [flagged, setFlagged] = useState<string[]>([])
  const [selectedLabels, setSelectedLabels] = useState<Record<string, string>>({})
  const [notes, setNotes] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState<boolean>(true)
  const [sessionLogs, setSessionLogs] = useState<Record<string, any[]>>({})
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})
  const [fullContext, setFullContext] = useState<Record<string, boolean>>({})

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.getJobStatus(jobId)
        setFlagged(res.data.flagged_sessions || [])
      } catch (e) {
        toast.error('Failed to load flagged sessions')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [jobId])

  // Lazy-load logs for a session when expanded the first time
  const ensureSessionLog = async (sessionId: string) => {
    if (sessionLogs[sessionId]) return
    try {
      const res = await api.getSessionLog(jobId, sessionId)
      const raw = (res.data?.events || res.data?.log || res.data) as any[]
      if (Array.isArray(raw)) {
        setSessionLogs((prev) => ({ ...prev, [sessionId]: raw }))
      }
    } catch (e) {
      // Silently ignore; UI will just not show details
    }
  }

  const submitResolution = async (sessionId: string) => {
    const label = selectedLabels[sessionId]
    const note = notes[sessionId] || ''
    if (!label) {
      toast.error('Select a label to resolve')
      return
    }
    try {
      await api.client.post(`/annotations/job/${jobId}/session/${sessionId}/resolve`, { label, note, dataset_name: datasetName })
      toast.success(`Resolved session ${sessionId}`)
      setFlagged(flagged.filter(s => s !== sessionId))
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Failed to resolve session')
    }
  }

  const resumeFromCheckpoint = async () => {
    try {
      // Requires the caller to start a new job with resume_job_id
      toast.success('You can now resume the job from the checkpoint via Configure → Start Annotation')
      if (onFinish) onFinish()
    } catch (e) {}
  }

  if (loading) {
    return <div className="text-gray-500">Loading flagged sessions…</div>
  }

  if (flagged.length === 0) {
    return (
      <div className="text-center">
        <p className="text-gray-600">No sessions require manual review.</p>
        <button onClick={onFinish} className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">Finish</button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {flagged.map((sessionId) => (
        <div key={sessionId} className="border border-gray-200 rounded-2xl p-6 bg-white">
          <div className="flex items-center justify-between">
            <div className="font-semibold text-gray-900">Session {sessionId}</div>
            <div className="flex items-center gap-3">
              <button
                onClick={async () => {
                  setExpanded((prev) => ({ ...prev, [sessionId]: !prev[sessionId] }))
                  if (!expanded[sessionId]) await ensureSessionLog(sessionId)
                }}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
              >
                {expanded[sessionId] ? 'Hide Details' : 'Show Details'}
              </button>
              <button
                onClick={() => submitResolution(sessionId)}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                Save Resolution
              </button>
            </div>
          </div>

          {expanded[sessionId] && (
            <div className="mt-4 space-y-4">
              {/* Relevant original session parts: flagged events + extended context or full session */}
              {(() => {
                const events = sessionLogs[sessionId] || []
                if (!events.length) return <div className="text-sm text-gray-500">No event log available.</div>

                // Build context indices (±3 around flagged) unless full context is toggled
                const indicesFlagged = events
                  .map((ev, i) => ({ ev, i }))
                  .filter(({ ev }) => ev?.flagged_for_review)
                  .map(({ i }) => i)
                let indices: number[]
                if (fullContext[sessionId]) {
                  indices = events.map((_, i) => i)
                } else {
                  const ctx = new Set<number>()
                  indicesFlagged.forEach((i) => {
                    for (let k = i - 3; k <= i + 3; k++) {
                      if (k >= 0 && k < events.length) ctx.add(k)
                    }
                  })
                  indices = Array.from(ctx.values()).sort((a, b) => a - b)
                }

                const getDomain = (url?: string) => {
                  try { return url ? new URL(url).hostname.replace('www.', '') : undefined } catch { return undefined }
                }

                return (
                  <>
                    <div className="flex items-center justify-between">
                      <div className="text-sm text-gray-600">
                        Showing {indices.length} of {events.length} events
                      </div>
                      <button
                        onClick={() => setFullContext(prev => ({ ...prev, [sessionId]: !prev[sessionId] }))}
                        className="px-3 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
                      >
                        {fullContext[sessionId] ? 'Show Flagged Context Only' : 'Show Full Session'}
                      </button>
                    </div>

                    <div className="space-y-3">
                      {indices.map((idx) => {
                        const ev = events[idx] || {}
                        const isFlagged = !!ev.flagged_for_review
                        const analyst = ev.analyst_label || ev.agent_decisions?.find((d: any) => d.agent_name === 'analyst')?.label
                        const critic = ev.critic_label || ev.agent_decisions?.find((d: any) => d.agent_name === 'critic')?.label
                        const finalLabel = ev.cognitive_label || ev.label
                        const disagree = ev.disagreement_score ?? ev.max_disagreement
                        const meta = ev.metadata || {}
                        const url = meta.url || ev.url
                        const domain = getDomain(url)
                        const action = (ev.action_type || '').toUpperCase()
                        const headerBadge = isFlagged ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'

                        return (
                          <div key={ev.event_id || idx} className="rounded-xl border border-gray-200 overflow-hidden">
                            <div className={`px-4 py-2 text-xs font-medium ${headerBadge} flex items-center justify-between`}>
                              <div className="flex items-center gap-3">
                                <span className="text-gray-500">{ev.timestamp || ev.event_timestamp || '-'}</span>
                                <span className="px-2 py-0.5 rounded bg-gray-900 text-white">{action || '-'}</span>
                                {domain && <span className="px-2 py-0.5 rounded bg-gray-200 text-gray-700">{domain}</span>}
                              </div>
                              {isFlagged && (
                                <span className="px-2 py-0.5 rounded bg-orange-100 text-orange-700">Flagged</span>
                              )}
                            </div>

                            <div className="p-4 grid md:grid-cols-12 gap-4">
                              {/* Content column */}
                              <div className="md:col-span-7 space-y-2">
                                {action === 'QUERY' ? (
                                  <div>
                                    <div className="text-xs text-gray-500">Query</div>
                                    <div className="text-gray-900 font-medium">{meta.query || ev.query || ev.content || '-'}</div>
                                  </div>
                                ) : action === 'CLICK' ? (
                                  <div className="space-y-1">
                                    {meta.title && (
                                      <div className="text-gray-900 font-medium">{meta.title}</div>
                                    )}
                                    <div className="text-gray-700">{ev.content || meta.snippet || '-'}</div>
                                    {url && (
                                      <a href={url} target="_blank" rel="noreferrer" className="text-xs text-blue-600 underline break-all">{url}</a>
                                    )}
                                  </div>
                                ) : (
                                  <div className="space-y-1">
                                    <div className="text-gray-900 font-medium">{meta.title || ev.title || '-'}</div>
                                    <div className="text-gray-700">{ev.content || meta.description || '-'}</div>
                                    {meta.rating !== undefined && (
                                      <div className="text-xs text-gray-600">Rating: {meta.rating}</div>
                                    )}
                                  </div>
                                )}
                              </div>

                              {/* Labels column */}
                              <div className="md:col-span-5">
                                <div className="space-y-2 text-sm">
                                  <div className="flex items-center justify-between">
                                    <span className="text-gray-600">Final</span>
                                    <span className="px-2 py-0.5 rounded bg-gray-900 text-white font-semibold">{finalLabel || '-'}</span>
                                  </div>
                                  <div className="flex items-center justify-between">
                                    <span className="text-gray-600">Analyst</span>
                                    <span className="px-2 py-0.5 rounded bg-gray-100 text-gray-800">{analyst || '-'}</span>
                                  </div>
                                  <div className="flex items-center justify-between">
                                    <span className="text-gray-600">Critic</span>
                                    <span className="px-2 py-0.5 rounded bg-gray-100 text-gray-800">{critic || '-'}</span>
                                  </div>
                                  {disagree !== undefined && (
                                    <div className="flex items-center justify-between">
                                      <span className="text-gray-600">Disagreement</span>
                                      <span className="text-gray-900 font-medium">{typeof disagree === 'number' ? disagree.toFixed(2) : disagree}</span>
                                    </div>
                                  )}
                                </div>

                                {/* Justifications (collapsible) */}
                                {(ev.analyst_justification || ev.critic_justification || ev.judge_justification) && (
                                  <details className="mt-3">
                                    <summary className="text-xs text-gray-600 cursor-pointer">Show justifications</summary>
                                    <div className="mt-2 space-y-2 text-xs text-gray-700">
                                      {ev.analyst_justification && (
                                        <div>
                                          <div className="font-semibold text-gray-900">Analyst</div>
                                          <p className="leading-relaxed">{ev.analyst_justification}</p>
                                        </div>
                                      )}
                                      {ev.critic_justification && (
                                        <div>
                                          <div className="font-semibold text-gray-900">Critic</div>
                                          <p className="leading-relaxed">{ev.critic_justification}</p>
                                        </div>
                                      )}
                                      {ev.judge_justification && (
                                        <div>
                                          <div className="font-semibold text-gray-900">Judge</div>
                                          <p className="leading-relaxed">{ev.judge_justification}</p>
                                        </div>
                                      )}
                                    </div>
                                  </details>
                                )}
                              </div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </>
                )
              })()}
            </div>
          )}

          <div className="mt-4 grid md:grid-cols-2 gap-3">
            {LABELS.map(l => (
              <label key={l.value} className={`border rounded-lg p-3 cursor-pointer ${selectedLabels[sessionId] === l.value ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}`}>
                <div className="flex items-start gap-3">
                  <input
                    type="radio"
                    name={`label-${sessionId}`}
                    className="mt-1"
                    checked={selectedLabels[sessionId] === l.value}
                    onChange={() => setSelectedLabels({ ...selectedLabels, [sessionId]: l.value })}
                  />
                  <div>
                    <div className="font-medium text-gray-900">{l.value}</div>
                    <div className="text-xs text-gray-600">{l.title} — {l.desc}</div>
                  </div>
                </div>
              </label>
            ))}
          </div>
          <textarea
            className="mt-3 w-full border border-gray-200 rounded-lg p-2 text-sm"
            placeholder="Add an optional note"
            value={notes[sessionId] || ''}
            onChange={(e) => setNotes({ ...notes, [sessionId]: e.target.value })}
          />
        </div>
      ))}

      <div className="flex justify-end gap-3">
        <button onClick={resumeFromCheckpoint} className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">Resume from Checkpoint</button>
        <button onClick={onFinish} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">Finish</button>
      </div>
    </div>
  )
}


