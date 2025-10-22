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
    <div className="card max-w-2xl mx-auto">
      <div className="text-center mb-6">
        <Upload className="w-16 h-16 mx-auto mb-4 text-primary-600" />
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Upload Your Dataset
        </h2>
        <p className="text-gray-600">
          Support for CSV and JSON formats. Compatible with AOL, Stack Overflow, MovieLens, and custom datasets.
        </p>
      </div>
      
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-primary-500 bg-primary-50'
            : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
        }`}
      >
        <input {...getInputProps()} />
        <FileText className="w-12 h-12 mx-auto mb-4 text-gray-400" />
        {isDragActive ? (
          <p className="text-lg text-primary-600">Drop the file here...</p>
        ) : (
          <>
            <p className="text-lg text-gray-700 mb-2">
              Drag and drop your file here, or click to browse
            </p>
            <p className="text-sm text-gray-500">
              Supported formats: CSV, JSON (Max 100MB)
            </p>
          </>
        )}
      </div>
      
      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <h3 className="font-semibold text-gray-900 mb-2">Required Fields:</h3>
        <ul className="text-sm text-gray-700 space-y-1">
          <li>• <code className="bg-white px-2 py-0.5 rounded">session_id</code> - Unique session identifier</li>
          <li>• <code className="bg-white px-2 py-0.5 rounded">timestamp</code> - Event timestamp</li>
          <li>• <code className="bg-white px-2 py-0.5 rounded">action_type</code> - QUERY, CLICK, RATE, etc.</li>
          <li>• <code className="bg-white px-2 py-0.5 rounded">content</code> - Query text or document content</li>
        </ul>
      </div>
    </div>
  )
}

