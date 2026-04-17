'use client'
import { useEffect, useState } from 'react'
import { useSession, signIn } from 'next-auth/react'
import { X } from 'lucide-react'

const KEY = 'traces:login_banner_dismissed'

export function LoginBanner() {
  const { status } = useSession()
  const [dismissed, setDismissed] = useState(true)
  useEffect(() => {
    setDismissed(localStorage.getItem(KEY) === '1')
  }, [])
  if (status === 'authenticated' || dismissed) return null
  return (
    <div className="max-w-6xl mx-auto mb-6 px-4 py-3 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-between">
      <p className="text-sm text-blue-900">
        Sign in with GitHub to save your configurations and view past runs. The tool works without an account too.
      </p>
      <div className="flex items-center gap-2">
        <button
          onClick={() => signIn('github')}
          className="text-sm font-medium px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700"
        >
          Sign in
        </button>
        <button
          onClick={() => { localStorage.setItem(KEY, '1'); setDismissed(true) }}
          aria-label="Dismiss"
          className="p-1 rounded hover:bg-blue-100"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
