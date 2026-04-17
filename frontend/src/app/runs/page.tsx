'use client'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useSession } from 'next-auth/react'
import { api } from '@/lib/api'
import type { RunListOut } from '@/types/auth'
import { Navigation } from '@/components/layout/Navigation'
import { Footer } from '@/components/layout/Footer'

export default function RunsPage() {
  const { status } = useSession()
  const [data, setData] = useState<RunListOut | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (status !== 'authenticated') return
    api.listRuns().then(r => setData(r.data)).catch(e => setError(String(e)))
  }, [status])

  if (status === 'unauthenticated') {
    return (
      <div className="min-h-screen flex flex-col">
        <Navigation />
        <main className="flex-1 container py-12 flex items-center justify-center">
          <p>
            Please <a href="/api/auth/signin" className="underline">sign in</a> to view your runs.
          </p>
        </main>
        <Footer />
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Navigation />
      <main className="flex-1 container py-12">
        <h1 className="text-3xl font-bold mb-6">My Annotation Runs</h1>
        {error && <p className="text-red-600">{error}</p>}
        {!data ? (
          <p>Loading…</p>
        ) : data.items.length === 0 ? (
          <p className="text-gray-500">
            No runs yet. <Link href="/annotator" className="underline">Start one</Link>.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-gray-500">
                <tr>
                  <th className="py-2 pr-4">Dataset</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2 pr-4">Sessions</th>
                  <th className="py-2 pr-4">Flagged</th>
                  <th className="py-2 pr-4">Resolved</th>
                  <th className="py-2 pr-4">Started</th>
                  <th className="py-2 pr-4"></th>
                </tr>
              </thead>
              <tbody>
                {data.items.map(r => (
                  <tr key={r.id} className="border-t">
                    <td className="py-2 pr-4">{r.dataset_filename}</td>
                    <td className="py-2 pr-4">{r.status}</td>
                    <td className="py-2 pr-4">{r.completed_sessions}/{r.total_sessions}</td>
                    <td className="py-2 pr-4">{r.flagged_count}</td>
                    <td className="py-2 pr-4">{r.resolved_count}</td>
                    <td className="py-2 pr-4">{r.started_at?.slice(0, 10) ?? '—'}</td>
                    <td className="py-2 pr-4">
                      <Link
                        href={`/annotator/${r.job_id}/annotate`}
                        className="text-blue-600 hover:underline"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
      <Footer />
    </div>
  )
}
