'use client'

import { Download, FileJson, FileSpreadsheet } from 'lucide-react'

interface ExportSectionProps {
  sessionId: string
}

export function ExportSection({ sessionId }: ExportSectionProps) {
  const handleExport = (format: 'csv' | 'json') => {
    // TODO: Implement actual export functionality
    console.log(`Exporting session ${sessionId} as ${format}`)
  }
  
  return (
    <div className="card">
      <div className="flex items-center space-x-2 mb-4">
        <Download className="w-5 h-5 text-gray-700" />
        <h2 className="text-xl font-semibold text-gray-900">
          Export Annotations
        </h2>
      </div>
      
      <p className="text-gray-600 mb-4">
        Download your annotated data in your preferred format
      </p>
      
      <div className="grid grid-cols-2 gap-4">
        <button
          onClick={() => handleExport('csv')}
          className="flex items-center justify-center space-x-2 p-4 border-2 border-gray-200 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-all"
        >
          <FileSpreadsheet className="w-6 h-6 text-green-600" />
          <span className="font-medium">CSV</span>
        </button>
        
        <button
          onClick={() => handleExport('json')}
          className="flex items-center justify-center space-x-2 p-4 border-2 border-gray-200 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-all"
        >
          <FileJson className="w-6 h-6 text-blue-600" />
          <span className="font-medium">JSON</span>
        </button>
      </div>
    </div>
  )
}

