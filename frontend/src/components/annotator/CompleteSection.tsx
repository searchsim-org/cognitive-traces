'use client'

import { useState, useEffect } from 'react'
import { Download, AlertTriangle } from 'lucide-react'
import { api } from '@/lib/api'
import { ExportSection } from './ExportSection'
import toast from 'react-hot-toast'

interface CompleteSectionProps {
  jobId: string
  uploadedDataset: {
    dataset_id: string
    filename: string
    total_sessions: number
    total_events: number
  }
  onReviewFlags: () => void
  onStartNew: () => void
}

export function CompleteSection({ jobId, uploadedDataset, onReviewFlags, onStartNew }: CompleteSectionProps) {
  const [jobStatus, setJobStatus] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchJobStatus = async () => {
      try {
        const response = await api.getJobStatus(jobId)
        setJobStatus(response.data)
      } catch (error) {
        console.error('Error fetching job status:', error)
        toast.error('Failed to load job status')
      } finally {
        setIsLoading(false)
      }
    }

    fetchJobStatus()
  }, [jobId])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  const hasErrors = jobStatus?.errors && jobStatus.errors.length > 0
  const completedSessions = jobStatus?.completed_sessions || 0
  const totalSessions = jobStatus?.total_sessions || 0
  const successRate = totalSessions > 0 ? (completedSessions / totalSessions) * 100 : 0
  const hasSuccessfulResults = completedSessions > 0

  return (
    <div className="space-y-8">
      {/* Status Message */}
      <div className="text-center py-12">
        <div className={`inline-flex items-center justify-center w-24 h-24 rounded-full ${hasSuccessfulResults ? 'bg-green-100' : 'bg-yellow-100'} mb-6`}>
          <span className="text-5xl">{hasSuccessfulResults ? '✓' : '⚠'}</span>
        </div>
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          {hasSuccessfulResults ? 'Annotation Complete!' : 'Annotation Finished with Errors'}
        </h2>
        <p className="text-lg text-gray-600 mb-2">
          {hasSuccessfulResults 
            ? `Successfully annotated ${completedSessions} of ${totalSessions} sessions (${successRate.toFixed(1)}%)`
            : `No sessions were successfully annotated. All ${totalSessions} sessions encountered errors.`
          }
        </p>
        {!hasSuccessfulResults && (
          <p className="text-sm text-red-600 mt-4">
            Please check your API keys and model configuration, then try again.
          </p>
        )}
      </div>

      {/* Error Summary */}
      {hasErrors && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-2xl p-6">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-6 h-6 text-yellow-600 flex-shrink-0 mt-1" />
            <div className="flex-1">
              <h3 className="font-bold text-yellow-900 mb-2">
                {jobStatus.errors.length} Error{jobStatus.errors.length > 1 ? 's' : ''} Occurred
              </h3>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {jobStatus.errors.slice(0, 10).map((error: string, idx: number) => (
                  <div key={idx} className="text-sm text-yellow-800 bg-white rounded px-3 py-2">
                    {error}
                  </div>
                ))}
                {jobStatus.errors.length > 10 && (
                  <p className="text-sm text-yellow-700 italic">
                    ... and {jobStatus.errors.length - 10} more errors
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Export Section - Only show if there are successful results */}
      {hasSuccessfulResults && (
        <ExportSection 
          jobId={jobId} 
          datasetName={uploadedDataset.filename.replace(/\.(csv|json)$/i, '')}
        />
      )}

      {/* Action Buttons */}
      <div className="flex justify-center gap-4 pt-4">
        {hasSuccessfulResults && (
          <button
            onClick={onReviewFlags}
            className="px-6 py-3 border border-gray-300 rounded-xl text-gray-700 hover:bg-gray-50"
          >
            Review Flagged Sessions
          </button>
        )}
        <button
          onClick={onStartNew}
          className="px-8 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 font-medium"
        >
          {hasSuccessfulResults ? 'Annotate Another Dataset' : 'Try Again with Different Settings'}
        </button>
      </div>
    </div>
  )
}

export default CompleteSection
