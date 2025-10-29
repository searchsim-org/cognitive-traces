'use client'

import { Clock, MousePointer, Search } from 'lucide-react'

interface SessionViewerProps {
  sessions: any[]
  selectedSession: any
  onSelectSession: (session: any) => void
}

export function SessionViewer({ sessions, selectedSession, onSelectSession }: SessionViewerProps) {
  return (
    <div className="p-10 rounded-3xl border border-gray-200 bg-white">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">
        Sessions
      </h2>
      
      <div className="space-y-4">
        {sessions.map((session) => (
          <div
            key={session.id}
            onClick={() => onSelectSession(session)}
            className={`p-6 rounded-2xl border-2 cursor-pointer transition-all ${
              selectedSession?.id === session.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-bold text-lg text-gray-900">{session.name}</h3>
              <span className="text-sm text-gray-500 font-medium">{session.events} events</span>
            </div>
            
            <div className="flex items-center space-x-6 text-sm text-gray-600">
              <div className="flex items-center space-x-2">
                <Clock className="w-4 h-4" />
                <span>2min 34s</span>
              </div>
              <div className="flex items-center space-x-2">
                <Search className="w-4 h-4" />
                <span>3 queries</span>
              </div>
              <div className="flex items-center space-x-2">
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

