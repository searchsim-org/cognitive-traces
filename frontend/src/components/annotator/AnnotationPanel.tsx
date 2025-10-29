'use client'

import { Brain, CheckCircle, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'

const cognitiveLabels = [
  { value: 'FollowingScent', label: 'Following Scent', bgColor: 'bg-green-500', textColor: 'text-green-500' },
  { value: 'ApproachingSource', label: 'Approaching Source', bgColor: 'bg-blue-500', textColor: 'text-blue-500' },
  { value: 'DietEnrichment', label: 'Diet Enrichment', bgColor: 'bg-purple-500', textColor: 'text-purple-500' },
]

interface AnnotationPanelProps {
  session: any
}

export function AnnotationPanel({ session }: AnnotationPanelProps) {
  return (
    <div className="p-10 rounded-3xl border border-gray-200 bg-white sticky top-24">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-12 h-12 rounded-xl bg-purple-500 flex items-center justify-center">
          <Brain className="w-6 h-6 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900">
          AI Annotation
        </h2>
      </div>
      
      <div className="space-y-8">
        <div>
          <h3 className="font-bold text-gray-900 mb-4">Event Timeline</h3>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="p-4 bg-gray-50 rounded-xl border border-gray-200">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-bold text-gray-900">Event {i}</span>
                  <span className="text-xs text-gray-500 font-medium">12:34:{i}0</span>
                </div>
                <div className={`inline-block px-3 py-1.5 rounded-lg ${cognitiveLabels[i - 1].bgColor} text-white text-xs font-bold`}>
                  {cognitiveLabels[i - 1].label}
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div>
          <h3 className="font-bold text-gray-900 mb-4">Agent Consensus</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-gray-900 font-medium">Analyst (Claude)</span>
              <CheckCircle className="w-5 h-5 text-green-500" />
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-gray-900 font-medium">Critic (GPT-4o)</span>
              <CheckCircle className="w-5 h-5 text-green-500" />
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-gray-900 font-medium">Judge (GPT-4o)</span>
              <CheckCircle className="w-5 h-5 text-green-500" />
            </div>
          </div>
        </div>
        
        <div className="p-4 bg-blue-50 rounded-xl border border-blue-100">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
            <div>
              <h4 className="font-bold text-blue-900 mb-1">
                Justification
              </h4>
              <p className="text-sm text-blue-800 leading-relaxed">
                User initiated search with clear intent, followed by targeted clicks indicating strong information scent.
              </p>
            </div>
          </div>
        </div>
        
        <Button className="w-full bg-gray-900 hover:bg-gray-800 text-white rounded-full py-6 text-base font-medium">
          Accept Annotation
        </Button>
      </div>
    </div>
  )
}

