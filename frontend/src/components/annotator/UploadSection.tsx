'use client'

import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText } from 'lucide-react'
import toast from 'react-hot-toast'

interface UploadSectionProps {
  onUploadComplete: (data: any) => void
}

export function UploadSection({ onUploadComplete }: UploadSectionProps) {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return
    
    // TODO: Implement actual file upload to backend
    toast.success(`File ${file.name} uploaded successfully`)
    
    // Mock data for now
    setTimeout(() => {
      onUploadComplete({
        sessions: [
          { id: '1', name: 'Session 1', events: 5 },
          { id: '2', name: 'Session 2', events: 8 },
        ]
      })
    }, 1000)
  }, [onUploadComplete])
  
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/json': ['.json'],
    },
    maxFiles: 1,
  })
  
  return (
    <div className="max-w-3xl mx-auto">
      <div className="p-10 rounded-3xl border border-gray-200 bg-white">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-blue-500 mb-6">
            <Upload className="w-10 h-10 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-3">
            Upload Your Dataset
          </h2>
          <p className="text-lg text-gray-600 leading-relaxed">
            Support for CSV and JSON formats. Compatible with AOL, Stack Overflow, MovieLens, and custom datasets.
          </p>
        </div>
        
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-2xl p-16 text-center cursor-pointer transition-all ${
            isDragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
          }`}
        >
          <input {...getInputProps()} />
          <FileText className="w-16 h-16 mx-auto mb-6 text-gray-400" />
          {isDragActive ? (
            <p className="text-xl text-blue-600 font-medium">Drop the file here...</p>
          ) : (
            <>
              <p className="text-xl text-gray-900 mb-2 font-medium">
                Drag and drop your file here, or click to browse
              </p>
              <p className="text-gray-500">
                Supported formats: CSV, JSON (Max 100MB)
              </p>
            </>
          )}
        </div>
        
        <div className="mt-8 p-6 bg-gray-50 rounded-2xl border border-gray-200">
          <h3 className="font-bold text-gray-900 mb-4">Required Fields:</h3>
          <ul className="text-gray-700 space-y-2">
            <li>• <code className="bg-white px-3 py-1 rounded border border-gray-200 font-mono text-sm">session_id</code> - Unique session identifier</li>
            <li>• <code className="bg-white px-3 py-1 rounded border border-gray-200 font-mono text-sm">timestamp</code> - Event timestamp</li>
            <li>• <code className="bg-white px-3 py-1 rounded border border-gray-200 font-mono text-sm">action_type</code> - QUERY, CLICK, RATE, etc.</li>
            <li>• <code className="bg-white px-3 py-1 rounded border border-gray-200 font-mono text-sm">content</code> - Query text or document content</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

