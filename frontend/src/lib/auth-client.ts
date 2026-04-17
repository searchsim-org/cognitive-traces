let cached: { token: string; expiresAt: number } | null = null

/** Returns a backend-bound JWT, cached in memory until ~60s before expiry.
 *  Returns `null` when there is no active session. */
export async function getBackendToken(): Promise<string | null> {
  const now = Math.floor(Date.now() / 1000)
  if (cached && cached.expiresAt - 60 > now) return cached.token

  const res = await fetch('/api/auth/backend-token', { credentials: 'include' })
  if (res.status === 401) {
    cached = null
    return null
  }
  if (!res.ok) throw new Error(`backend-token failed: ${res.status}`)

  const data = (await res.json()) as { token: string; expiresAt: number }
  cached = { token: data.token, expiresAt: Math.max(data.expiresAt, now + 60) }
  return cached.token
}

export function clearBackendTokenCache() {
  cached = null
}
