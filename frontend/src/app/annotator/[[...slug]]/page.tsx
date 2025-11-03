'use client'

import { useState, useEffect, Suspense } from 'react'
import dynamic from 'next/dynamic'
import { useRouter, useParams } from 'next/navigation'
import { Navigation } from '@/components/layout/Navigation'
import { Footer } from '@/components/layout/Footer'
import { api } from '@/lib/api'
import toast from 'react-hot-toast'

// Dynamic imports for components that may have SSR issues
const FileUploader = dynamic(() => import('@/components/annotator/FileUploader').then(mod => ({ default: mod.FileUploader })), { ssr: false })
const DatasetReview = dynamic(() => import('@/components/annotator/DatasetReview').then(mod => ({ default: mod.DatasetReview })), { ssr: false })
const LLMConfigPanel = dynamic(() => import('@/components/annotator/LLMConfigPanel').then(mod => ({ default: mod.LLMConfigPanel })), { ssr: false })
const ProgressTracker = dynamic(() => import('@/components/annotator/ProgressTracker').then(mod => ({ default: mod.ProgressTracker })), { ssr: false })
const FlaggedSessions = dynamic(() => import('@/components/annotator/FlaggedSessions').then(mod => ({ default: mod.FlaggedSessions })), { ssr: false })
const ExportSection = dynamic(() => import('@/components/annotator/ExportSection').then(mod => ({ default: mod.ExportSection })), { ssr: false })

type Step = 'upload' | 'review' | 'configure' | 'annotate' | 'resolve' | 'complete'

interface UploadedDataset {
  dataset_id: string
  filename: string
  total_sessions: number
  total_events: number
  sessions: any[]
}

function AnnotatorContent() {
  const router = useRouter()
  const params = useParams()
  
  // Parse URL segments: /annotator/[step] or /annotator/[jobId]/[step]
  const slug = params.slug as string[] | undefined
  
  let urlStep: Step = 'upload'
  let urlJobId: string | null = null
  
  if (slug && slug.length > 0) {
    if (slug.length === 1) {
      // /annotator/upload, /annotator/review, etc.
      urlStep = slug[0] as Step
    } else if (slug.length === 2) {
      // /annotator/[jobId]/annotate
      urlJobId = slug[0]
      urlStep = slug[1] as Step
    }
  }
  
  const [currentStep, setCurrentStep] = useState<Step>(urlStep)
  
  const [uploadedDataset, setUploadedDataset] = useState<UploadedDataset | null>(null)
  const [llmConfig, setLLMConfig] = useState<any>(null)
  const [jobId, setJobId] = useState<string | null>(urlJobId)
  const [sessionIds, setSessionIds] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [flaggedSessionsCount, setFlaggedSessionsCount] = useState<number>(0)

  // Restore dataset metadata from localStorage on mount
  useEffect(() => {
    // Clean up old full-dataset localStorage key (migration)
    if (localStorage.getItem('annotator_dataset')) {
      localStorage.removeItem('annotator_dataset')
      console.log('[Cleanup] Removed old full dataset from localStorage')
    }
    
    const savedMeta = localStorage.getItem('annotator_dataset_meta')
    if (savedMeta) {
      try {
        const meta = JSON.parse(savedMeta)
        console.log('[Restore] Dataset metadata restored:', meta.filename)
        setUploadedDataset(meta)
      } catch (e) {
        console.error('[Restore] Failed to parse saved metadata:', e)
        localStorage.removeItem('annotator_dataset_meta')
      }
    }
  }, [])

  // Save only dataset metadata to localStorage (not full sessions data)
  useEffect(() => {
    if (uploadedDataset) {
      try {
        const meta = {
          dataset_id: uploadedDataset.dataset_id,
          filename: uploadedDataset.filename,
          total_sessions: uploadedDataset.total_sessions,
          total_events: uploadedDataset.total_events,
        }
        localStorage.setItem('annotator_dataset_meta', JSON.stringify(meta))
        console.log('[Save] Dataset metadata saved to localStorage')
      } catch (e) {
        console.warn('[Save] Could not save metadata to localStorage (quota exceeded?):', e)
        // Silently fail - not critical
      }
    }
  }, [uploadedDataset])
  
  // Update URL when step changes
  const updateStep = (newStep: Step, newJobId?: string | null) => {
    setCurrentStep(newStep)
    
    // Use provided jobId or existing one
    const activeJobId = newJobId !== undefined ? newJobId : jobId
    
    // Construct URL based on step and jobId
    let path = '/annotator'
    if (newStep === 'upload') {
      path = '/annotator'
    } else if (activeJobId && (newStep === 'annotate' || newStep === 'resolve' || newStep === 'complete')) {
      // Use jobId in URL for job-specific steps
      path = `/annotator/${activeJobId}/${newStep}`
    } else {
      // Simple step URL for pre-job steps
      path = `/annotator/${newStep}`
    }
    
    router.push(path, { scroll: false })
  }


  // Handle file upload
  const handleFileUpload = async (file: File) => {
    setIsLoading(true)
    try {
      toast.loading('Uploading and analyzing file...', { id: 'upload' })
      
      const response = await api.uploadDataset(file, 'custom')
      const data = response.data
      
      console.log('[Upload] Received dataset:', data)
      console.log('[Upload] Sessions count:', data.sessions?.length)
      
      // Clear old dataset metadata from localStorage before setting new one
      localStorage.removeItem('annotator_dataset_meta')
      
      setUploadedDataset(data)
      updateStep('review')
      
      toast.success(`Found ${data.total_sessions} sessions with ${data.total_events} events`, { 
        id: 'upload' 
      })
    } catch (error: any) {
      console.error('Upload error:', error)
      toast.error(error.response?.data?.detail || 'Failed to upload file', { id: 'upload' })
    } finally {
      setIsLoading(false)
    }
  }

  // Handle starting annotation job
  const handleStartAnnotation = async () => {
    if (!uploadedDataset || !llmConfig) return
    
    setIsLoading(true)
    try {
      const response = await api.startAnnotationJob(
        uploadedDataset.dataset_id,
        llmConfig,
        uploadedDataset.filename.replace(/\.(csv|json)$/i, '')
      )
      
      const newJobId = response.data.job_id
      setJobId(newJobId)
      setSessionIds(response.data.session_ids || [])
      updateStep('annotate', newJobId)
      
      toast.success('Annotation job started!')
    } catch (error: any) {
      console.error('Start job error:', error)
      toast.error(error.response?.data?.detail || 'Failed to start annotation')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-white">
      <Navigation />
      
      <main className="flex-1">
        <div className="container py-12 md:py-16">
          {/* Header */}
          <div className="text-center mb-12 max-w-4xl mx-auto">
            <h1 className="text-5xl md:text-6xl font-bold tracking-tight text-gray-900 mb-4">
              Annotator Tool
            </h1>
            <p className="text-xl text-gray-600 font-light">
              AI-assisted annotation for inferring cognitive states from user behavior
            </p>
          </div>

          {/* Progress Steps - Hidden on resolve step */}
          {currentStep !== 'resolve' && (
          <div className="max-w-6xl mx-auto mb-12">
            <div className="flex items-center justify-between">
              {['Upload', 'Review', 'Configure', 'Annotate', 'Resolve Flags', 'Complete'].map((step, index) => {
                const stepValues: Step[] = ['upload', 'review', 'configure', 'annotate', 'resolve', 'complete']
                const currentStepIndex = stepValues.indexOf(currentStep)
                const isActive = currentStepIndex === index
                const isCompleted = currentStepIndex > index
                
                // Determine if step is clickable (can go back, but not forward)
                const isClickable = isCompleted || isActive
                
                // Validate if we can navigate to this step
                const canNavigate = () => {
                  if (index === 0) return true // Can always go to upload
                  if (index === 1) return uploadedDataset !== null // Need dataset for review
                  if (index === 2) return uploadedDataset !== null // Need dataset for configure
                  if (index === 3) return uploadedDataset !== null && llmConfig !== null && jobId !== null // annotate
                  if (index === 4) return jobId !== null // resolve flags
                  if (index === 5) return true // complete
                  return false
                }
                
                const handleStepClick = () => {
                  if (!isClickable) return
                  if (!canNavigate()) {
                    toast.error('Please complete previous steps first')
                    return
                  }
                  
                  const targetStep = stepValues[index]
                  
                  // Special handling for going back to upload - clear job
                  if (targetStep === 'upload') {
                    setJobId(null)
                    updateStep(targetStep, null)
                  } else {
                    updateStep(targetStep)
                  }
                }
                
                return (
                  <div key={step} className="flex-1 flex items-center">
                    <div className="flex flex-col items-center flex-1">
                      <div
                        onClick={handleStepClick}
                        className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all ${
                          isCompleted
                            ? 'bg-green-500 text-white cursor-pointer hover:bg-green-600 hover:scale-110'
                            : isActive
                            ? 'bg-blue-500 text-white cursor-pointer'
                            : 'bg-gray-200 text-gray-500 cursor-not-allowed'
                        }`}
                        title={isClickable ? `Go to ${step}` : `Complete previous steps to unlock`}
                      >
                        {isCompleted ? '✓' : index + 1}
                      </div>
                      <span className={`mt-2 text-sm ${isActive ? 'text-blue-600 font-medium' : 'text-gray-500'}`}>
                        {step}
                      </span>
                    </div>
                    {index < 5 && (
                      <div className={`h-0.5 flex-1 mx-2 ${isCompleted ? 'bg-green-500' : 'bg-gray-200'}`} />
                    )}
                  </div>
                )
              })}
            </div>
          </div>
          )}

          {/* Main Content */}
          <div className="max-w-6xl mx-auto">
            {/* Step 1: Upload */}
            {currentStep === 'upload' && (
              <FileUploader onUpload={handleFileUpload} isLoading={isLoading} />
            )}

            {/* Step 2: Review Sessions */}
            {currentStep === 'review' && uploadedDataset ? (
              <>
                {console.log('[Annotator] Rendering DatasetReview with:', {
                  datasetId: uploadedDataset.dataset_id,
                  filename: uploadedDataset.filename,
                  totalSessions: uploadedDataset.total_sessions,
                  totalEvents: uploadedDataset.total_events
                })}
                <DatasetReview
                  datasetId={uploadedDataset.dataset_id}
                  filename={uploadedDataset.filename}
                  totalSessions={uploadedDataset.total_sessions}
                  totalEvents={uploadedDataset.total_events}
                  onBack={() => {
                    setUploadedDataset(null)
                    setJobId(null)
                    localStorage.removeItem('annotator_dataset_meta')
                    updateStep('upload', null)
                  }}
                  onContinue={() => updateStep('configure')}
                />
              </>
            ) : currentStep === 'review' ? (
              <div className="text-center py-12">
                <p className="text-gray-500">No dataset uploaded. Please upload a dataset first.</p>
                <button
                  onClick={() => updateStep('upload', null)}
                  className="mt-4 px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700"
                >
                  Go to Upload
                </button>
              </div>
            ) : null}

            {/* Step 3: Configure LLM Models */}
            {currentStep === 'configure' && (
              <div className="space-y-6">
                <LLMConfigPanel onConfigComplete={(config) => {
                  setLLMConfig(config)
                  // Auto-advance when config is complete
                }} />
                
                <div className="flex justify-between">
                  <button
                    onClick={() => updateStep('review')}
                    className="px-6 py-3 border border-gray-300 rounded-xl text-gray-700 hover:bg-gray-50"
                  >
                    Back to Review
                  </button>
                  <button
                    onClick={handleStartAnnotation}
                    disabled={!llmConfig || isLoading}
                    className="px-8 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoading ? 'Starting...' : 'Start Annotation'}
                  </button>
                </div>
              </div>
            )}

            {/* Step 4: Annotation Progress */}
            {currentStep === 'annotate' && jobId && uploadedDataset && (
              <ProgressTracker
                jobId={jobId}
                totalSessions={uploadedDataset.total_sessions}
                sessionIds={sessionIds}
                onComplete={async () => {
                  // Check if there are flagged sessions
                  try {
                    const response = await api.getJobStatus(jobId)
                    const flaggedCount = response.data.flagged_sessions?.length || 0
                    setFlaggedSessionsCount(flaggedCount)
                    
                    // Skip resolve step if no flagged sessions
                    if (flaggedCount === 0) {
                      toast.success('No sessions flagged for review. Proceeding to completion!')
                      updateStep('complete')
                    } else {
                      updateStep('resolve')
                    }
                  } catch (error) {
                    // Fallback to resolve step on error
                    updateStep('resolve')
                  }
                }}
                onStopped={async () => {
                  // Check if there are flagged sessions
                  try {
                    const response = await api.getJobStatus(jobId)
                    const flaggedCount = response.data.flagged_sessions?.length || 0
                    setFlaggedSessionsCount(flaggedCount)
                    
                    // Skip resolve step if no flagged sessions
                    if (flaggedCount === 0) {
                      updateStep('complete')
                    } else {
                      updateStep('resolve')
                    }
                  } catch (error) {
                    // Fallback to resolve step on error
                    updateStep('resolve')
                  }
                }}
              />
            )}

            {/* Step 5: Resolve Flags */}
            {currentStep === 'resolve' && jobId && (
              <div className="space-y-6">
                <div className="bg-white rounded-3xl p-8">
                  <FlaggedSessions jobId={jobId} datasetName={uploadedDataset?.filename.replace(/\.(csv|json)$/i, '') || 'dataset'} onFinish={() => updateStep('complete')} />
                </div>
              </div>
            )}

            {/* Step 6: Complete */}
            {currentStep === 'complete' && jobId && uploadedDataset && (
              <div className="space-y-8">
                {/* Success Message */}
                <div className="text-center py-12">
                  <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-green-100 mb-6">
                    <span className="text-5xl">✓</span>
                  </div>
                  <h2 className="text-3xl font-bold text-gray-900 mb-4">
                    Annotation Complete!
                  </h2>
                  <p className="text-lg text-gray-600 mb-2">
                    Your cognitive traces have been successfully generated.
                  </p>
                  <p className="text-sm text-gray-500">
                    Download your annotated data below or start a new annotation job.
                  </p>
                </div>

                {/* Export Section */}
                <ExportSection 
                  jobId={jobId} 
                  datasetName={uploadedDataset.filename.replace(/\.(csv|json)$/i, '')}
                />

                {/* Action Buttons */}
                <div className="flex justify-center gap-4 pt-4">
                  <button
                    onClick={() => updateStep('resolve')}
                    className="px-6 py-3 border border-gray-300 rounded-xl text-gray-700 hover:bg-gray-50"
                  >
                    Review Flagged Sessions
                  </button>
                  <button
                    onClick={() => {
                      setUploadedDataset(null)
                      setLLMConfig(null)
                      setJobId(null)
                      setSessionIds([])
                      localStorage.removeItem('annotator_dataset_meta')
                      updateStep('upload', null)
                    }}
                    className="px-8 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 font-medium"
                  >
                    Annotate Another Dataset
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
      
      <Footer />
    </div>
  )
}

export default function AnnotatorPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading annotator...</p>
        </div>
      </div>
    }>
      <AnnotatorContent />
    </Suspense>
  )
}
