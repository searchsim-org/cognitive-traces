'use client'
import { useEffect, useState } from 'react'
import { useSession } from 'next-auth/react'
import { api } from '@/lib/api'
import type { PresetOut } from '@/types/auth'

type Props = { onLoad: (config: Record<string, unknown>) => void }

export function PresetSelect({ onLoad }: Props) {
  const { status } = useSession()
  const [presets, setPresets] = useState<PresetOut[]>([])
  useEffect(() => {
    if (status !== 'authenticated') return
    api.listPresets().then(r => setPresets(r.data)).catch(() => {})
  }, [status])
  if (status !== 'authenticated' || presets.length === 0) return null
  return (
    <select
      defaultValue=""
      onChange={e => {
        const p = presets.find(x => x.id === e.target.value)
        if (p) onLoad(p.config_json)
      }}
      className="rounded-lg border px-3 py-2 text-sm"
    >
      <option value="" disabled>Load a saved configuration…</option>
      {presets.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
    </select>
  )
}
