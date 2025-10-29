'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { ChevronLeft, ChevronRight, Eye } from 'lucide-react'
import toast from 'react-hot-toast'

interface DatasetReviewProps {
  datasetId: string
  filename: string
  totalSessions: number
  totalEvents: number
  onBack: () => void
  onContinue: () => void
}

export function DatasetReview({
  datasetId,
  filename,
  totalSessions,
  totalEvents,
  onBack,
  onContinue
}: DatasetReviewProps) {
  const [page, setPage] = useState(1)
  const [limit] = useState(10)
  const [sessions, setSessions] = useState<any[]>([])
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [expandedSession, setExpandedSession] = useState<string | null>(null)

  useEffect(() => {
    const fetchSessions = async () => {
      if (!datasetId) {
        console.error('[DatasetReview] No datasetId provided')
        toast.error('Dataset ID is missing')
        setLoading(false)
        return
      }
      
      setLoading(true)
      console.log('[DatasetReview] Fetching dataset info:', datasetId, 'page:', page)
      try {
        const response = await api.getDatasetInfo(datasetId, page, limit)
        console.log('[DatasetReview] Received sessions:', response.data.sessions?.length)
        setSessions(response.data.sessions || [])
        setTotalPages(response.data.total_pages || 1)
      } catch (error: any) {
        toast.error('Failed to load dataset preview')
        console.error('[DatasetReview] Error fetching dataset info:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchSessions()
  }, [datasetId, page, limit])

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-3xl border border-gray-200 p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Dataset Overview</h2>
            <p className="text-gray-600 mt-1">Review extracted sessions before annotation</p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-blue-600">{totalSessions.toLocaleString()}</div>
            <div className="text-sm text-gray-500">Sessions</div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="p-4 bg-gray-50 rounded-xl">
            <div className="text-sm text-gray-600">Filename</div>
            <div className="text-lg font-medium text-gray-900 truncate">{filename}</div>
          </div>
          <div className="p-4 bg-gray-50 rounded-xl">
            <div className="text-sm text-gray-600">Total Sessions</div>
            <div className="text-lg font-medium text-gray-900">{totalSessions.toLocaleString()}</div>
          </div>
          <div className="p-4 bg-gray-50 rounded-xl">
            <div className="text-sm text-gray-600">Total Events</div>
            <div className="text-lg font-medium text-gray-900">{totalEvents.toLocaleString()}</div>
          </div>
        </div>

        {/* Sessions Preview */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-gray-900">Sessions Preview</h3>
            <div className="text-sm text-gray-500">Page {page} of {totalPages}</div>
          </div>

          {loading ? (
            <div className="text-center py-8 text-gray-500">Loading sessions...</div>
          ) : sessions.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p className="mb-2">No sessions found in this dataset.</p>
              <p className="text-sm">Please check the uploaded file format.</p>
            </div>
          ) : (
            <>
              {sessions.map((session) => (
                <div
                  key={session.session_id}
                  className="border border-gray-200 rounded-xl p-4 hover:border-gray-300 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="font-bold text-gray-900">{session.session_id}</span>
                        <span className="px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 text-xs font-medium">
                          {session.num_events} events
                        </span>
                      </div>
                      {session.start_time && (
                        <div className="text-xs text-gray-500">
                          {session.start_time} → {session.end_time}
                        </div>
                      )}
                    </div>
                    <button
                      onClick={() => setExpandedSession(expandedSession === session.session_id ? null : session.session_id)}
                      className="px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
                    >
                      <Eye className="w-4 h-4" />
                      {expandedSession === session.session_id ? 'Hide' : 'Preview'}
                    </button>
                  </div>

                  {expandedSession === session.session_id && session.events_preview && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <div className="text-xs text-gray-600 mb-2">First {session.events_preview.length} events:</div>
                      <div className="space-y-2">
                        {session.events_preview.map((event: any, idx: number) => (
                          <div key={idx} className="p-3 bg-gray-50 rounded-lg text-sm">
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-medium text-gray-900">{event.action_type || 'EVENT'}</span>
                              <span className="text-xs text-gray-500">{event.timestamp || event.event_timestamp}</span>
                            </div>
                            <div className="text-gray-700 text-xs truncate">{event.content || event.query || '-'}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-4">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                <ChevronLeft className="w-4 h-4" />
                Previous
              </button>
              <div className="px-4 py-2 text-sm text-gray-600">
                Page {page} of {totalPages}
              </div>
              <button
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page === totalPages}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                Next
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="mt-8 flex justify-between">
          <button
            onClick={onBack}
            className="px-6 py-3 border border-gray-300 rounded-xl text-gray-700 hover:bg-gray-50"
          >
            Upload Different File
          </button>
          <button
            onClick={onContinue}
            className="px-8 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 font-medium"
          >
            Continue to Configuration
          </button>
        </div>
      </div>
    </div>
  )
}

