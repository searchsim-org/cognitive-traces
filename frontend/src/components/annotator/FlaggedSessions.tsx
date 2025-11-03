'use client'

import { useEffect, useState, useRef } from 'react'
import { api } from '@/lib/api'
import toast from 'react-hot-toast'
import { ChevronLeft, ChevronRight, Eye, AlertTriangle, CheckCircle2 } from 'lucide-react'

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
  const [currentIndex, setCurrentIndex] = useState<number>(0)
  const [currentFlaggedEventIndex, setCurrentFlaggedEventIndex] = useState<Record<string, number>>({}) // Track which flagged event we're on per session
  const [selectedLabels, setSelectedLabels] = useState<Record<string, string>>({})
  const [notes, setNotes] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState<boolean>(true)
  const [sessionLogs, setSessionLogs] = useState<Record<string, any[]>>({})
  const [showHistory, setShowHistory] = useState<boolean>(false)
  const [fullContext, setFullContext] = useState<Record<string, boolean>>({})
  const [resolvedSessions, setResolvedSessions] = useState<Set<string>>(new Set())
  const currentEventRef = useRef<HTMLDivElement>(null)

  // Load resolved sessions from localStorage on mount
  useEffect(() => {
    const savedResolved = localStorage.getItem(`resolved_sessions_${jobId}`)
    if (savedResolved) {
      try {
        const parsed = JSON.parse(savedResolved)
        setResolvedSessions(new Set(parsed))
      } catch (e) {
        console.error('Failed to parse saved resolved sessions:', e)
      }
    }
  }, [jobId])

  // Save resolved sessions to localStorage whenever it changes
  useEffect(() => {
    if (resolvedSessions.size > 0) {
      localStorage.setItem(`resolved_sessions_${jobId}`, JSON.stringify(Array.from(resolvedSessions)))
    }
  }, [resolvedSessions, jobId])

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.getJobStatus(jobId)
        const flaggedSessions = res.data.flagged_sessions || []
        setFlagged(flaggedSessions)
        
        // Load saved resolved sessions
        const savedResolved = localStorage.getItem(`resolved_sessions_${jobId}`)
        let resolved = new Set<string>()
        if (savedResolved) {
          try {
            resolved = new Set(JSON.parse(savedResolved))
            setResolvedSessions(resolved)
          } catch (e) {
            console.error('Failed to parse saved resolved sessions:', e)
          }
        }
        
        // Find first unresolved session and start there
        let startIndex = 0
        for (let i = 0; i < flaggedSessions.length; i++) {
          if (!resolved.has(flaggedSessions[i])) {
            startIndex = i
            break
          }
        }
        
        setCurrentIndex(startIndex)
        
        // Pre-load the starting session
        if (flaggedSessions.length > 0) {
          await ensureSessionLog(flaggedSessions[startIndex])
        }
      } catch (e) {
        toast.error('Failed to load flagged sessions')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [jobId])

  // Keyboard navigation
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLTextAreaElement || e.target instanceof HTMLInputElement) return
      
      if (e.key === 'ArrowLeft' && currentIndex > 0) {
        e.preventDefault()
        handlePrevious()
      } else if (e.key === 'ArrowRight' && currentIndex < flagged.length - 1) {
        e.preventDefault()
        handleNext()
      }
    }
    
    window.addEventListener('keydown', handleKeyPress)
    return () => window.removeEventListener('keydown', handleKeyPress)
  }, [currentIndex, flagged.length])

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

  const handleNext = async () => {
    if (currentIndex < flagged.length - 1) {
      const nextIndex = currentIndex + 1
      setCurrentIndex(nextIndex)
      setShowHistory(false)
      await ensureSessionLog(flagged[nextIndex])
    }
  }

  const handlePrevious = async () => {
    if (currentIndex > 0) {
      const prevIndex = currentIndex - 1
      setCurrentIndex(prevIndex)
      setShowHistory(false)
      await ensureSessionLog(flagged[prevIndex])
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
      await api.resolveSession(jobId, sessionId, label, note, datasetName)
      
      const events = sessionLogs[sessionId] || []
      const flaggedIndices = events
        .map((ev, i) => ({ ev, i }))
        .filter(({ ev }) => ev?.flagged_for_review)
        .map(({ i }) => i)
      
      const currentFlaggedIdx = currentFlaggedEventIndex[sessionId] || 0
      
      // Check if there are more flagged events in this session
      if (currentFlaggedIdx < flaggedIndices.length - 1) {
        // Move to next flagged event in same session
        setCurrentFlaggedEventIndex({
          ...currentFlaggedEventIndex,
          [sessionId]: currentFlaggedIdx + 1
        })
        toast.success(`Event resolved. ${flaggedIndices.length - currentFlaggedIdx - 1} more in this session.`)
        // Clear selection for next event
        const newSelectedLabels = { ...selectedLabels }
        delete newSelectedLabels[sessionId]
        setSelectedLabels(newSelectedLabels)
      } else {
        // All flagged events in this session are resolved
        toast.success(`Session ${sessionId} fully resolved!`)
        setResolvedSessions(new Set([...resolvedSessions, sessionId]))
        
        // Move to next session or finish
        if (currentIndex < flagged.length - 1) {
          await handleNext()
        } else {
          // All resolved
          toast.success('All flagged sessions resolved!')
          setTimeout(() => onFinish?.(), 1500)
        }
      }
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed to resolve session')
    }
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

  const sessionId = flagged[currentIndex]
  const events = sessionLogs[sessionId] || []
  const isResolved = resolvedSessions.has(sessionId)

  // Get all flagged event indices
  const indicesFlagged = events
    .map((ev, i) => ({ ev, i }))
    .filter(({ ev }) => ev?.flagged_for_review)
    .map(({ i }) => i)
  
  // Track which flagged event we're currently annotating
  const currentFlaggedIdx = currentFlaggedEventIndex[sessionId] || 0
  const currentFlaggedEventIdx = indicesFlagged[currentFlaggedIdx]
  
  let indices: number[]
  if (fullContext[sessionId]) {
    // Show all events
    indices = events.map((_, i) => i)
  } else {
    // Show ONLY the current flagged event being annotated
    indices = currentFlaggedEventIdx !== undefined ? [currentFlaggedEventIdx] : []
  }

  const getDomain = (url?: string) => {
    try { return url ? new URL(url).hostname.replace('www.', '') : undefined } catch { return undefined }
  }

  const autoAnnotateWithFinal = async () => {
    // Use the final label from the judge for this session
    const flaggedEvents = events.filter(ev => ev.flagged_for_review)
    if (flaggedEvents.length === 0) {
      toast.error('No flagged events found')
      return
    }
    
    // Take the most common final label from flagged events
    const labels = flaggedEvents.map(ev => ev.cognitive_label || ev.label).filter(Boolean)
    if (labels.length === 0) {
      toast.error('No final labels found for auto-annotation')
      return
    }
    
    // Find the most common label
    const labelCounts: Record<string, number> = {}
    labels.forEach(label => {
      labelCounts[label] = (labelCounts[label] || 0) + 1
    })
    
    const mostCommonLabel = Object.entries(labelCounts)
      .sort((a, b) => b[1] - a[1])[0][0]
    
    // Auto-select and immediately save
    setSelectedLabels({ ...selectedLabels, [sessionId]: mostCommonLabel })
    toast.success(`Auto-selected: ${mostCommonLabel}. Saving...`)
    
    // Automatically submit the resolution
    try {
      await api.resolveSession(jobId, sessionId, mostCommonLabel, 'Auto-annotated using final label', datasetName)
      setResolvedSessions(new Set([...resolvedSessions, sessionId]))
      toast.success(`Session ${sessionId} resolved!`)
      
      // Move to next session or finish
      if (currentIndex < flagged.length - 1) {
        await handleNext()
      } else {
        toast.success('All flagged sessions resolved!')
        setTimeout(() => onFinish?.(), 1500)
      }
    } catch (e: any) {
      console.error('Failed to auto-annotate session:', e)
      toast.error(e?.response?.data?.detail || 'Failed to auto-annotate session')
    }
  }
  
  const toggleFullContext = (sessionId: string) => {
    const newValue = !fullContext[sessionId]
    setFullContext(prev => ({ ...prev, [sessionId]: newValue }))
    
    // If toggling to full context, scroll to current event after a brief delay
    if (newValue) {
      setTimeout(() => {
        currentEventRef.current?.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'center' 
        })
      }, 100)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-3xl border border-gray-200 p-8 text-center">
        <h2 className="text-3xl font-bold text-gray-900">Review Flagged Sessions</h2>
        <p className="text-gray-600 mt-2 max-w-2xl mx-auto">
          Review sessions with high agent disagreement and finalize cognitive labels. Your decisions will update the final annotations.
        </p>
        
        {/* Progress Bar */}
        <div className="mt-6 max-w-2xl mx-auto">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              {resolvedSessions.size} of {flagged.length} resolved
            </span>
            <span className="text-sm font-medium text-gray-700">
              Session {currentIndex + 1} of {flagged.length}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className="h-full bg-green-600 transition-all duration-300"
              style={{ width: `${(resolvedSessions.size / flagged.length) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Navigation Controls */}
      <div className="bg-white rounded-3xl border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <button
            onClick={handlePrevious}
            disabled={currentIndex === 0}
            className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition-all ${
              currentIndex === 0
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            <ChevronLeft className="w-5 h-5" />
            Previous
          </button>

          <div className="text-sm text-gray-500">
            Use ← → arrow keys to navigate
          </div>

          <button
            onClick={handleNext}
            disabled={currentIndex === flagged.length - 1}
            className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition-all ${
              currentIndex === flagged.length - 1
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            Next
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Current Session */}
      <div className={`rounded-3xl border-2 p-8 ${
        isResolved 
          ? 'bg-gradient-to-br from-green-50 via-white to-white border-green-300' 
          : 'bg-gradient-to-br from-orange-50 via-white to-white border-orange-200'
      }`}>
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
              isResolved ? 'bg-green-500' : 'bg-orange-500'
            }`}>
              {isResolved ? (
                <CheckCircle2 className="w-6 h-6 text-white" />
              ) : (
                <AlertTriangle className="w-6 h-6 text-white" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-xl font-bold text-gray-900">Session {sessionId}</h3>
                {isResolved && (
                  <span className="px-3 py-1 bg-green-100 text-green-700 text-xs font-bold rounded-full">
                    RESOLVED
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-600">
                {events.length} events • Flagged event {currentFlaggedIdx + 1} of {indicesFlagged.length}
                {isResolved && <span className="ml-2 text-green-600">• You can still override</span>}
              </p>
            </div>
          </div>
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="flex items-center gap-2 px-4 py-2 border-2 border-gray-300 rounded-lg text-sm hover:bg-gray-50 font-medium"
          >
            <Eye className="w-4 h-4" />
            {showHistory ? 'Hide History' : 'Show Agent History'}
          </button>
        </div>

        {/* Agent History (when toggled) */}
        {showHistory && (
          <div className="mb-6 p-4 bg-white rounded-xl border border-gray-200">
            <h4 className="font-bold text-gray-900 mb-3">Agent Interactions</h4>
            <div className="flex items-center gap-3">
              {['Analyst', 'Critic', 'Judge'].map((agent, i) => (
                <div key={agent} className="flex-1 flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    agent === 'Analyst' ? 'bg-purple-100' : agent === 'Critic' ? 'bg-orange-100' : 'bg-blue-100'
                  }`}>
                    <span className="text-sm font-bold">{i + 1}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-gray-900">{agent}</div>
                    <div className="text-xs text-gray-600 truncate">
                      {agent === 'Analyst' && 'Initial analysis'}
                      {agent === 'Critic' && 'Review & refinement'}
                      {agent === 'Judge' && 'Final decision'}
                    </div>
                  </div>
                  <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0" />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Events to Annotate */}
        <div className="space-y-4 mb-6">
          {events.length === 0 ? (
            <div className="text-sm text-gray-500 text-center py-8">Loading session events...</div>
          ) : (
            <>
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-bold text-gray-900">
                  {fullContext[sessionId] ? 'Full Session Context' : 'Current Flagged Event'}
                  <span className="ml-2 text-sm text-gray-500">
                    {fullContext[sessionId] ? `(${events.length} events)` : `(Event ${currentFlaggedIdx + 1}/${indicesFlagged.length})`}
                  </span>
                </h4>
                <button
                  onClick={() => toggleFullContext(sessionId)}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 font-medium"
                >
                  {fullContext[sessionId] ? 'Show Current Event' : 'Show Full Session'}
                </button>
              </div>

              <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
                {indices.map((idx) => {
                  const ev = events[idx] || {}
                  // Check if this is the current flagged event
                  const isCurrentFlagged = idx === currentFlaggedEventIdx
                  // Only show orange border when in single event view
                  const isFlagged = !fullContext[sessionId] && isCurrentFlagged
                  const analyst = ev.analyst_label || ev.agent_decisions?.find((d: any) => d.agent_name === 'analyst')?.label
                  const critic = ev.critic_label || ev.agent_decisions?.find((d: any) => d.agent_name === 'critic')?.label
                  const finalLabel = ev.cognitive_label || ev.label
                  const disagree = ev.disagreement_score ?? ev.max_disagreement
                  const meta = ev.metadata || {}
                  const url = meta.url || ev.url
                  const domain = getDomain(url)
                  const action = (ev.action_type || '').toUpperCase()
                  
                  // In full context mode, highlight current event with different style
                  const borderStyle = isFlagged 
                    ? 'border-orange-300 shadow-md' 
                    : (fullContext[sessionId] && isCurrentFlagged)
                      ? 'border-blue-400 shadow-lg ring-2 ring-blue-200'
                      : 'border-gray-200'
                  const headerBadge = isFlagged 
                    ? 'bg-orange-100 text-orange-800 border-orange-300' 
                    : (fullContext[sessionId] && isCurrentFlagged)
                      ? 'bg-blue-100 text-blue-800 border-blue-300'
                      : 'bg-gray-50 text-gray-700 border-gray-200'

                  return (
                    <div 
                      key={ev.event_id || idx} 
                      ref={isCurrentFlagged ? currentEventRef : null}
                      className={`rounded-xl border-2 overflow-hidden transition-all ${borderStyle}`}
                    >
                      <div className={`px-4 py-2 text-xs font-medium ${headerBadge} flex items-center justify-between`}>
                        <div className="flex items-center gap-3">
                          <span className="text-gray-600">{ev.timestamp || ev.event_timestamp || '-'}</span>
                          <span className="px-2 py-0.5 rounded bg-gray-900 text-white">{action || '-'}</span>
                          {domain && <span className="px-2 py-0.5 rounded bg-gray-200 text-gray-700">{domain}</span>}
                        </div>
                        {isFlagged && (
                          <span className="px-2 py-0.5 rounded bg-orange-500 text-white font-semibold">FLAGGED</span>
                        )}
                        {fullContext[sessionId] && isCurrentFlagged && (
                          <span className="px-2 py-0.5 rounded bg-blue-500 text-white font-semibold">CURRENT</span>
                        )}
                      </div>

                      <div className="p-4 grid md:grid-cols-12 gap-4 bg-white">
                        {/* Content column */}
                        <div className="md:col-span-7 space-y-2">
                          {action === 'QUERY' ? (
                            <div>
                              <div className="text-xs text-gray-500 font-medium">Query</div>
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
                              <span className="text-gray-600 font-medium">Final</span>
                              <span className="px-2 py-0.5 rounded bg-gray-900 text-white font-semibold">{finalLabel || '-'}</span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-gray-600">Analyst</span>
                              <span className="px-2 py-0.5 rounded bg-purple-100 text-purple-800">{analyst || '-'}</span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-gray-600">Critic</span>
                              <span className="px-2 py-0.5 rounded bg-orange-100 text-orange-800">{critic || '-'}</span>
                            </div>
                            {disagree !== undefined && (
                              <div className="flex items-center justify-between">
                                <span className="text-gray-600">Disagreement</span>
                                <span className="text-gray-900 font-bold">{typeof disagree === 'number' ? disagree.toFixed(2) : disagree}</span>
                              </div>
                            )}
                          </div>

                          {/* Justifications (collapsible) */}
                          {(ev.analyst_justification || ev.critic_justification || ev.judge_justification) && (
                            <details className="mt-3">
                              <summary className="text-xs text-blue-600 cursor-pointer font-medium hover:text-blue-700">View justifications</summary>
                              <div className="mt-2 space-y-2 text-xs text-gray-700">
                                {ev.analyst_justification && (
                                  <div className="p-2 bg-purple-50 rounded">
                                    <div className="font-semibold text-purple-900">Analyst</div>
                                    <p className="leading-relaxed">{ev.analyst_justification}</p>
                                  </div>
                                )}
                                {ev.critic_justification && (
                                  <div className="p-2 bg-orange-50 rounded">
                                    <div className="font-semibold text-orange-900">Critic</div>
                                    <p className="leading-relaxed">{ev.critic_justification}</p>
                                  </div>
                                )}
                                {ev.judge_justification && (
                                  <div className="p-2 bg-blue-50 rounded">
                                    <div className="font-semibold text-blue-900">Judge</div>
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
          )}
        </div>

        {/* Label Selection */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-bold text-gray-900">Select Correct Label</h4>
            <button
              onClick={autoAnnotateWithFinal}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm font-medium transition-colors"
            >
              <CheckCircle2 className="w-4 h-4" />
              Auto-Annotate (Use Final Label)
            </button>
          </div>
          <div className="grid md:grid-cols-2 gap-3">
            {LABELS.map(l => (
              <label key={l.value} className={`border-2 rounded-xl p-4 cursor-pointer transition-all ${selectedLabels[sessionId] === l.value ? 'border-blue-500 bg-blue-50 shadow-md' : 'border-gray-200 hover:border-gray-300'}`}>
                <div className="flex items-start gap-3">
                  <input
                    type="radio"
                    name={`label-${sessionId}`}
                    className="mt-1 w-4 h-4"
                    checked={selectedLabels[sessionId] === l.value}
                    onChange={() => setSelectedLabels({ ...selectedLabels, [sessionId]: l.value })}
                  />
                  <div>
                    <div className="font-bold text-gray-900">{l.value}</div>
                    <div className="text-xs text-gray-600 mt-1">{l.title}</div>
                    <div className="text-xs text-gray-500 mt-1">{l.desc}</div>
                  </div>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Notes */}
        <div className="mb-6">
          <label className="block font-bold text-gray-900 mb-2">Optional Notes</label>
          <textarea
            className="w-full border-2 border-gray-200 rounded-xl p-4 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Add any comments or notes about your decision..."
            rows={3}
            value={notes[sessionId] || ''}
            onChange={(e) => setNotes({ ...notes, [sessionId]: e.target.value })}
          />
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-4 border-t-2 border-gray-200">
          <button
            onClick={onFinish}
            className="px-6 py-3 border-2 border-gray-300 rounded-xl text-gray-700 hover:bg-gray-50 font-medium"
          >
            Finish Later
          </button>
          <button
            onClick={() => submitResolution(sessionId)}
            disabled={!selectedLabels[sessionId]}
            className={`px-8 py-3 rounded-xl font-bold transition-all flex items-center gap-2 ${
              selectedLabels[sessionId]
                ? 'bg-green-600 text-white hover:bg-green-700'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            }`}
          >
            <CheckCircle2 className="w-5 h-5" />
            Save & {currentIndex < flagged.length - 1 ? 'Next' : 'Finish'}
          </button>
        </div>
      </div>
    </div>
  )
}


