'use client'

import { Clock, MousePointer, Search } from 'lucide-react'

interface SessionViewerProps {
  sessions: any[]
  selectedSession: any
  onSelectSession: (session: any) => void
}

export function SessionViewer({ sessions, selectedSession, onSelectSession }: SessionViewerProps) {
  return (
    <div className="card">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">
        Sessions
      </h2>
      
      <div className="space-y-3">
        {sessions.map((session) => (
          <div
            key={session.id}
            onClick={() => onSelectSession(session)}
            className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
              selectedSession?.id === session.id
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-gray-900">{session.name}</h3>
              <span className="text-sm text-gray-500">{session.events} events</span>
            </div>
            
            <div className="flex items-center space-x-4 text-sm text-gray-600">
              <div className="flex items-center space-x-1">
                <Clock className="w-4 h-4" />
                <span>2min 34s</span>
              </div>
              <div className="flex items-center space-x-1">
                <Search className="w-4 h-4" />
                <span>3 queries</span>
              </div>
              <div className="flex items-center space-x-1">
                <MousePointer className="w-4 h-4" />
                <span>2 clicks</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

