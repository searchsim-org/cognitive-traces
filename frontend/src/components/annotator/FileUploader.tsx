'use client'

import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, Loader2 } from 'lucide-react'

interface FileUploaderProps {
  onUpload: (file: File) => void
  isLoading: boolean
}

export function FileUploader({ onUpload, isLoading }: FileUploaderProps) {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (file) {
      onUpload(file)
    }
  }, [onUpload])
  
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/json': ['.json'],
    },
    maxFiles: 1,
    disabled: isLoading,
  })
  
  return (
    <div className="max-w-3xl mx-auto">
      <div className="p-10 rounded-3xl border border-gray-200 bg-white">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-blue-500 mb-6">
            {isLoading ? (
              <Loader2 className="w-10 h-10 text-white animate-spin" />
            ) : (
              <Upload className="w-10 h-10 text-white" />
            )}
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-3">
            Upload Your Dataset
          </h2>
          <p className="text-lg text-gray-600 leading-relaxed">
            {isLoading 
              ? 'Analyzing your file and extracting sessions...'
              : 'Support for CSV and JSON formats. Compatible with AOL, Stack Overflow, MovieLens, and custom datasets.'
            }
          </p>
        </div>
        
        {!isLoading && (
          <>
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
              <h3 className="font-bold text-gray-900 mb-4">Required CSV Fields:</h3>
              <ul className="text-gray-700 space-y-2">
                <li>• <code className="bg-white px-3 py-1 rounded border border-gray-200 font-mono text-sm">session_id</code> - Unique session identifier</li>
                <li>• <code className="bg-white px-3 py-1 rounded border border-gray-200 font-mono text-sm">timestamp</code> - Event timestamp</li>
                <li>• <code className="bg-white px-3 py-1 rounded border border-gray-200 font-mono text-sm">action_type</code> - QUERY, CLICK, RATE, etc.</li>
                <li>• <code className="bg-white px-3 py-1 rounded border border-gray-200 font-mono text-sm">content</code> - Query text or document content</li>
              </ul>
            </div>
          </>
        )}
        
        {isLoading && (
          <div className="mt-8 p-6 bg-blue-50 rounded-2xl border border-blue-200 text-center">
            <p className="text-blue-800 font-medium">
              Please wait while we analyze your dataset structure and extract all sessions...
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

