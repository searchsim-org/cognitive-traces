'use client'

import { useState } from 'react'
import { Navigation } from '@/components/layout/Navigation'
import { UploadSection } from '@/components/annotator/UploadSection'
import { SessionViewer } from '@/components/annotator/SessionViewer'
import { AnnotationPanel } from '@/components/annotator/AnnotationPanel'
import { ExportSection } from '@/components/annotator/ExportSection'

export default function AnnotatorPage() {
  const [selectedSession, setSelectedSession] = useState<any>(null)
  const [sessions, setSessions] = useState<any[]>([])

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Cognitive Traces Annotator
          </h1>
          <p className="mt-2 text-gray-600">
            AI-assisted annotation tool for inferring cognitive states from user behavior logs
          </p>
        </div>

        {!sessions.length ? (
          <UploadSection onUploadComplete={(data) => setSessions(data.sessions)} />
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <SessionViewer
                sessions={sessions}
                selectedSession={selectedSession}
                onSelectSession={setSelectedSession}
              />
              {selectedSession && (
                <ExportSection sessionId={selectedSession.id} />
              )}
            </div>
            
            <div className="lg:col-span-1">
              {selectedSession && (
                <AnnotationPanel session={selectedSession} />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

