'use client'

import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, Loader2, ArrowRight, Database } from 'lucide-react'

interface FileUploaderProps {
  onUpload: (file: File) => void
  isLoading: boolean
}

export function FileUploader({ onUpload, isLoading }: FileUploaderProps) {
  const [isLoadingExample, setIsLoadingExample] = useState(false)

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
      'application/xml': ['.xml'],
    },
    maxFiles: 1,
    disabled: isLoading || isLoadingExample,
  })

  const loadExampleDataset = async () => {
    setIsLoadingExample(true)
    try {
      // Fetch the example dataset from the public folder
      const response = await fetch('/example-datasets/aol_1k.csv')
      if (!response.ok) {
        throw new Error('Failed to load example dataset')
      }
      
      const blob = await response.blob()
      const file = new File([blob], 'aol_1k_example.csv', { type: 'text/csv' })
      onUpload(file)
    } catch (error) {
      console.error('Error loading example dataset:', error)
      alert('Failed to load example dataset. Please try uploading your own file.')
    } finally {
      setIsLoadingExample(false)
    }
  }
  
  return (
    <div className="max-w-3xl mx-auto">
      {/* Dataset Converter CTA (visible above upload) */}
      {!isLoading && (
        <div className="mb-6 p-6 rounded-2xl border border-yellow-200 bg-yellow-50">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h3 className="font-bold text-2xl text-yellow-900 mb-1">Dataset Converter</h3>
              <p className="text-yellow-800 text-md">
                Your dataset doesn't match the required fields? <br/>Convert it by mapping columns (CSV/JSON/XML).
              </p>
            </div>
            <a
              href="/converter"
              className="inline-flex items-center justify-center px-5 py-3 rounded-full bg-yellow-600 text-white hover:bg-yellow-700 text-lg font-medium"
            >
              Open Converter
              <ArrowRight className="ml-2 w-5 h-5" />
            </a>
          </div>
        </div>
      )}

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
        
        {!isLoading && !isLoadingExample && (
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
                  Supported formats: CSV, JSON, XML (Max 100MB)
                  </p>
                </>
              )}
            </div>

            {/* Example Dataset Option */}
            <div className="mt-6 text-center">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-200"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-white text-gray-500">Or try with example data</span>
                </div>
              </div>
              
              <button
                onClick={loadExampleDataset}
                disabled={isLoadingExample}
                className="mt-4 inline-flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-xl font-medium hover:bg-green-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Database className="w-5 h-5" />
                Load Example Dataset (AOL Search - 1000 sessions)
              </button>
              <p className="mt-2 text-xs text-gray-500">
                Pre-loaded search sessions with QUERY, SERP_VIEW, and CLICK events
              </p>
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
        
        {(isLoading || isLoadingExample) && (
          <div className="mt-8 p-6 bg-blue-50 rounded-2xl border border-blue-200 text-center">
            <p className="text-blue-800 font-medium">
              {isLoadingExample 
                ? 'Loading example dataset...'
                : 'Please wait while we analyze your dataset structure and extract all sessions...'
              }
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

