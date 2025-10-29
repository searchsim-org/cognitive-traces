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
    <div className="p-10 rounded-3xl border border-gray-200 bg-white">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-12 h-12 rounded-xl bg-amber-500 flex items-center justify-center">
          <Download className="w-6 h-6 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900">
          Export Annotations
        </h2>
      </div>
      
      <p className="text-gray-600 mb-6 leading-relaxed">
        Download your annotated data in your preferred format
      </p>
      
      <div className="grid grid-cols-2 gap-4">
        <button
          onClick={() => handleExport('csv')}
          className="flex flex-col items-center justify-center gap-3 p-6 border-2 border-gray-200 rounded-2xl hover:border-gray-300 hover:bg-gray-50 transition-all"
        >
          <div className="w-12 h-12 rounded-xl bg-green-500 flex items-center justify-center">
            <FileSpreadsheet className="w-6 h-6 text-white" />
          </div>
          <span className="font-bold text-gray-900">CSV</span>
        </button>
        
        <button
          onClick={() => handleExport('json')}
          className="flex flex-col items-center justify-center gap-3 p-6 border-2 border-gray-200 rounded-2xl hover:border-gray-300 hover:bg-gray-50 transition-all"
        >
          <div className="w-12 h-12 rounded-xl bg-blue-500 flex items-center justify-center">
            <FileJson className="w-6 h-6 text-white" />
          </div>
          <span className="font-bold text-gray-900">JSON</span>
        </button>
      </div>
    </div>
  )
}

