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
        <div key={sessionId} className="border border-gray-200 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div className="font-semibold text-gray-900">Session {sessionId}</div>
            <button
              onClick={() => submitResolution(sessionId)}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              Save Resolution
            </button>
          </div>
          <div className="mt-3 grid md:grid-cols-2 gap-3">
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


