'use client'

import { Brain, CheckCircle, AlertCircle } from 'lucide-react'

const cognitiveLabels = [
  { value: 'FollowingScent', label: 'Following Scent', color: 'bg-green-100 text-green-700' },
  { value: 'ApproachingSource', label: 'Approaching Source', color: 'bg-blue-100 text-blue-700' },
  { value: 'DietEnrichment', label: 'Diet Enrichment', color: 'bg-purple-100 text-purple-700' },
  { value: 'PoorScent', label: 'Poor Scent', color: 'bg-yellow-100 text-yellow-700' },
  { value: 'LeavingPatch', label: 'Leaving Patch', color: 'bg-red-100 text-red-700' },
  { value: 'ForagingSuccess', label: 'Foraging Success', color: 'bg-emerald-100 text-emerald-700' },
]

interface AnnotationPanelProps {
  session: any
}

export function AnnotationPanel({ session }: AnnotationPanelProps) {
  return (
    <div className="card sticky top-6">
      <div className="flex items-center space-x-2 mb-6">
        <Brain className="w-6 h-6 text-primary-600" />
        <h2 className="text-xl font-semibold text-gray-900">
          AI Annotation
        </h2>
      </div>
      
      <div className="space-y-6">
        <div>
          <h3 className="font-semibold text-gray-900 mb-3">Event Timeline</h3>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Event {i}</span>
                  <span className="text-xs text-gray-500">12:34:{i}0</span>
                </div>
                <div className={`inline-block px-2 py-1 rounded text-xs font-medium ${cognitiveLabels[i - 1].color}`}>
                  {cognitiveLabels[i - 1].label}
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div>
          <h3 className="font-semibold text-gray-900 mb-3">Agent Consensus</h3>
          <div className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Analyst (Claude):</span>
              <CheckCircle className="w-5 h-5 text-green-500" />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Critic (GPT-4o):</span>
              <CheckCircle className="w-5 h-5 text-green-500" />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Judge (GPT-4o):</span>
              <CheckCircle className="w-5 h-5 text-green-500" />
            </div>
          </div>
        </div>
        
        <div className="p-3 bg-blue-50 rounded-lg">
          <div className="flex items-start space-x-2">
            <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
            <div>
              <h4 className="font-semibold text-blue-900 text-sm mb-1">
                Justification
              </h4>
              <p className="text-sm text-blue-800">
                User initiated search with clear intent, followed by targeted clicks indicating strong information scent.
              </p>
            </div>
          </div>
        </div>
        
        <button className="w-full btn-primary">
          Accept Annotation
        </button>
      </div>
    </div>
  )
}

