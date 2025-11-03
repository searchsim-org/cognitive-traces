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
          disabled={isExporting !== null}
          className="flex flex-col items-center justify-center gap-3 p-6 border-2 border-gray-200 rounded-2xl hover:border-gray-300 hover:bg-gray-50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isExporting === 'csv' ? (
            <Loader2 className="w-12 h-12 text-green-500 animate-spin" />
          ) : (
            <div className="w-12 h-12 rounded-xl bg-green-500 flex items-center justify-center">
              <FileSpreadsheet className="w-6 h-6 text-white" />
            </div>
          )}
          <span className="font-bold text-gray-900">CSV</span>
        </button>
        
        <button
          onClick={() => handleExport('json')}
          disabled={isExporting !== null}
          className="flex flex-col items-center justify-center gap-3 p-6 border-2 border-gray-200 rounded-2xl hover:border-gray-300 hover:bg-gray-50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isExporting === 'json' ? (
            <Loader2 className="w-12 h-12 text-blue-500 animate-spin" />
          ) : (
            <div className="w-12 h-12 rounded-xl bg-blue-500 flex items-center justify-center">
              <FileJson className="w-6 h-6 text-white" />
            </div>
          )}
          <span className="font-bold text-gray-900">JSON</span>
        </button>
      </div>
    </div>
  )
}

