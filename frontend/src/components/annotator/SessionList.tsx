'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight, Clock, Activity } from 'lucide-react'

interface Session {
  session_id: string
  num_events: number
  start_time: string
  end_time: string
  events: Event[]
}

interface Event {
  event_id: string
  timestamp: string
  action_type: string
  content: string
  metadata?: any
}

interface SessionListProps {
  sessions: Session[]
}

export function SessionList({ sessions }: SessionListProps) {
  const [expandedSessions, setExpandedSessions] = useState<Set<string>>(new Set())
  const [selectedSession, setSelectedSession] = useState<string | null>(null)

  const toggleSession = (sessionId: string) => {
    const newExpanded = new Set(expandedSessions)
    if (newExpanded.has(sessionId)) {
      newExpanded.delete(sessionId)
      if (selectedSession === sessionId) {
        setSelectedSession(null)
      }
    } else {
      newExpanded.add(sessionId)
      setSelectedSession(sessionId)
    }
    setExpandedSessions(newExpanded)
  }

  const parseContent = (content: string) => {
    try {
      return JSON.parse(content)
    } catch {
      return content
    }
  }

  return (
    <div className="space-y-3">
      <div className="max-h-[600px] overflow-y-auto pr-2">
        {sessions.map((session) => {
          const isExpanded = expandedSessions.has(session.session_id)
          const isSelected = selectedSession === session.session_id

          return (
            <div
              key={session.session_id}
              className={`border rounded-xl transition-all ${
                isSelected
                  ? 'border-blue-500 shadow-sm'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              {/* Session Header */}
              <button
                onClick={() => toggleSession(session.session_id)}
                className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors rounded-xl"
              >
                <div className="flex items-center gap-4">
                  <div className={`transition-transform ${isExpanded ? 'rotate-0' : ''}`}>
                    {isExpanded ? (
                      <ChevronDown className="w-5 h-5 text-gray-600" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-gray-600" />
                    )}
                  </div>
                  
                  <div className="text-left">
                    <div className="font-semibold text-gray-900">
                      Session: {session.session_id}
                    </div>
                    <div className="text-sm text-gray-500 mt-1 flex items-center gap-4">
                      <span className="flex items-center gap-1">
                        <Activity className="w-4 h-4" />
                        {session.num_events} events
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {new Date(session.start_time).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                    session.num_events > 10
                      ? 'bg-green-100 text-green-700'
                      : 'bg-blue-100 text-blue-700'
                  }`}>
                    {session.num_events} events
                  </span>
                </div>
              </button>

              {/* Session Details (Accordion Content) */}
              {isExpanded && (
                <div className="px-6 pb-4 border-t border-gray-100">
                  <div className="mt-4 space-y-3">
                    {session.events.map((event, index) => {
                      const parsedContent = parseContent(event.content)
                      const isObject = typeof parsedContent === 'object'

                      return (
                        <div
                          key={event.event_id}
                          className="bg-gray-50 rounded-lg p-4 border border-gray-200"
                        >
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex items-center gap-3">
                              <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-blue-500 text-white text-xs font-bold">
                                {index + 1}
                              </span>
                              <div>
                                <div className="font-medium text-gray-900">
                                  {event.action_type}
                                </div>
                                <div className="text-xs text-gray-500">
                                  {new Date(event.timestamp).toLocaleTimeString()}
                                </div>
                              </div>
                            </div>
                            <span className="text-xs font-mono text-gray-400">
                              {event.event_id.substring(0, 12)}...
                            </span>
                          </div>
                          
                          <div className="mt-3 pl-10">
                            <div className="text-sm text-gray-700">
                              {isObject ? (
                                <div className="space-y-1">
                                  {Object.entries(parsedContent).map(([key, value]) => (
                                    <div key={key} className="flex gap-2">
                                      <span className="font-medium text-gray-600">{key}:</span>
                                      <span className="text-gray-800">
                                        {typeof value === 'object' 
                                          ? JSON.stringify(value) 
                                          : String(value)
                                        }
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <p className="line-clamp-2">{String(parsedContent)}</p>
                              )}
                            </div>
                            
                            {event.metadata && Object.keys(event.metadata).length > 0 && (
                              <details className="mt-2">
                                <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                                  Metadata
                                </summary>
                                <pre className="mt-1 text-xs bg-white p-2 rounded border border-gray-200 overflow-x-auto">
                                  {JSON.stringify(event.metadata, null, 2)}
                                </pre>
                              </details>
                            )}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {sessions.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No sessions found in the uploaded file.
        </div>
      )}
    </div>
  )
}

