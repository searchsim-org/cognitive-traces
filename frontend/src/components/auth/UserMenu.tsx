'use client'
import { useState } from 'react'
import Link from 'next/link'
import { signOut, useSession } from 'next-auth/react'
import { clearBackendTokenCache } from '@/lib/auth-client'

export function UserMenu() {
  const { data } = useSession()
  const [open, setOpen] = useState(false)
  if (!data?.user) return null

  const avatar = (data.user as any).image as string | undefined
  return (
    <div className="relative">
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-2 rounded-full px-2 py-1 hover:bg-gray-100"
      >
        {avatar && <img src={avatar} alt="" className="w-8 h-8 rounded-full" />}
        <span className="text-sm font-medium">{data.user.name ?? 'Account'}</span>
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg border shadow-md z-50">
          <Link
            href="/runs"
            onClick={() => setOpen(false)}
            className="block px-4 py-2 text-sm hover:bg-gray-50"
          >
            My Runs
          </Link>
          <button
            onClick={() => { clearBackendTokenCache(); signOut() }}
            className="w-full text-left block px-4 py-2 text-sm hover:bg-gray-50"
          >
            Sign out
          </button>
        </div>
      )}
    </div>
  )
}
