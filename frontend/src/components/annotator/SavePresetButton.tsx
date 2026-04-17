'use client'
import { useState } from 'react'
import { useSession } from 'next-auth/react'
import toast from 'react-hot-toast'
import { api } from '@/lib/api'

type Props = { config: Record<string, unknown> }

export function SavePresetButton({ config }: Props) {
  const { status } = useSession()
  const [saving, setSaving] = useState(false)
  if (status !== 'authenticated') return null
  return (
    <button
      disabled={saving}
      onClick={async () => {
        const name = window.prompt('Preset name?')
        if (!name) return
        setSaving(true)
        try {
          await api.createPreset({ name, config_json: config })
          toast.success('Preset saved')
        } catch (e: any) {
          toast.error(e?.response?.data?.detail ?? 'Failed to save preset')
        } finally {
          setSaving(false)
        }
      }}
      className="rounded-lg border px-3 py-2 text-sm hover:bg-gray-50 disabled:opacity-50"
    >
      Save current as preset
    </button>
  )
}
