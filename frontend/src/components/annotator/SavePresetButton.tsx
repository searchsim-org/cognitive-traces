'use client'
import { useEffect, useRef, useState } from 'react'
import { useSession } from 'next-auth/react'
import { X } from 'lucide-react'
import toast from 'react-hot-toast'
import { api } from '@/lib/api'

type Props = { config: Record<string, unknown> }

export function SavePresetButton({ config }: Props) {
  const { status } = useSession()
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [saving, setSaving] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!open) return
    inputRef.current?.focus()
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !saving) closeDialog()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, saving])

  if (status !== 'authenticated') return null

  const closeDialog = () => {
    setOpen(false)
    setName('')
    setDescription('')
  }

  const handleSave = async () => {
    const trimmed = name.trim()
    if (!trimmed) {
      toast.error('Please enter a name for the preset')
      inputRef.current?.focus()
      return
    }
    setSaving(true)
    try {
      await api.createPreset({
        name: trimmed,
        description: description.trim() || undefined,
        config_json: config,
      })
      toast.success('Preset saved')
      closeDialog()
    } catch (e: any) {
      toast.error(e?.response?.data?.detail ?? 'Failed to save preset')
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="rounded-lg border px-3 py-2 text-sm hover:bg-gray-50"
      >
        Save current as preset
      </button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
          onClick={(e) => {
            if (e.target === e.currentTarget && !saving) closeDialog()
          }}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="save-preset-title"
            className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6"
          >
            <div className="flex items-start justify-between mb-4">
              <h3 id="save-preset-title" className="text-lg font-bold text-gray-900">
                Save configuration as preset
              </h3>
              <button
                onClick={closeDialog}
                disabled={saving}
                aria-label="Close"
                className="p-1 rounded hover:bg-gray-100 disabled:opacity-50"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-sm text-gray-600 mb-4">
              Saves model selections, strategy, parameters, and prompts. API keys are
              never sent to the server — they stay in your browser.
            </p>

            <label className="block mb-3">
              <span className="block text-sm font-medium text-gray-700 mb-1">Name</span>
              <input
                ref={inputRef}
                value={name}
                onChange={(e) => setName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !saving) handleSave()
                }}
                placeholder="e.g. Sonnet + GPT-4o, sliding window"
                maxLength={100}
                disabled={saving}
                className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
              />
            </label>

            <label className="block mb-5">
              <span className="block text-sm font-medium text-gray-700 mb-1">
                Description <span className="text-gray-400 font-normal">(optional)</span>
              </span>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="What this preset is good for…"
                maxLength={500}
                rows={2}
                disabled={saving}
                className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm resize-none"
              />
            </label>

            <div className="flex justify-end gap-2">
              <button
                onClick={closeDialog}
                disabled={saving}
                className="px-4 py-2 text-sm rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving || !name.trim()}
                className="px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? 'Saving…' : 'Save preset'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
