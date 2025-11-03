'use client'

import { useState } from 'react'
import { Download, FileJson, FileSpreadsheet, Loader2 } from 'lucide-react'
import { api } from '@/lib/api'
import toast from 'react-hot-toast'

interface ExportSectionProps {
  jobId: string
  datasetName: string
}

export function ExportSection({ jobId, datasetName }: ExportSectionProps) {
  const [isExporting, setIsExporting] = useState<'csv' | 'json' | null>(null)

  const handleExport = async (format: 'csv' | 'json') => {
    setIsExporting(format)
    try {
      toast.loading(`Preparing ${format.toUpperCase()} export...`, { id: 'export' })
      
      const response = format === 'csv' 
        ? await api.exportCsv({ dataset: datasetName })
        : await api.exportJson({ dataset: datasetName })
      
      // Create blob and download
      const blob = new Blob([response.data], { 
        type: format === 'csv' ? 'text/csv' : 'application/json' 
      })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${datasetName}_cognitive_traces.${format}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      toast.success(`Downloaded ${format.toUpperCase()} file`, { id: 'export' })
    } catch (error: any) {
      console.error('Export error:', error)
      toast.error(`Failed to export ${format.toUpperCase()}`, { id: 'export' })
    } finally {
      setIsExporting(null)
    }
  }
  
  return (
    <div className="p-10 rounded-3xl border border-gray-200 bg-white">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-12 h-12 rounded-xl bg-green-500 flex items-center justify-center">
          <Download className="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            Download Your Results
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            Cognitive traces with full annotations
          </p>
        </div>
      </div>
      
      {/* Primary CSV Download Button */}
      <button
        onClick={() => handleExport('csv')}
        disabled={isExporting !== null}
        className="w-full py-4 px-6 bg-green-600 hover:bg-green-700 text-white rounded-xl font-semibold text-lg flex items-center justify-center gap-3 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isExporting === 'csv' ? (
          <>
            <Loader2 className="w-6 h-6 animate-spin" />
            <span>Preparing Download...</span>
          </>
        ) : (
          <>
            <FileSpreadsheet className="w-6 h-6" />
            <span>Download CSV File</span>
          </>
        )}
      </button>
      
      <div className="mt-4 text-center">
        <p className="text-xs text-gray-500 mb-3">
          Includes session IDs, events, cognitive labels, justifications, and review flags
        </p>
        
        {/* Optional JSON Download Link */}
        <button
          onClick={() => handleExport('json')}
          disabled={isExporting !== null}
          className="text-sm text-blue-600 hover:text-blue-700 underline decoration-dotted underline-offset-4 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-1.5"
        >
          {isExporting === 'json' ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Preparing...</span>
            </>
          ) : (
            <>
              <FileJson className="w-3.5 h-3.5" />
              <span>Also download summary report (JSON)</span>
            </>
          )}
        </button>
      </div>
    </div>
  )
}

