import { getToken } from 'next-auth/jwt'
import jwt from 'jsonwebtoken'
import { NextRequest } from 'next/server'
import { jwtDecode } from '@/lib/auth-options'

const BACKEND_TOKEN_TTL_SECONDS = 60 * 15 // 15 minutes

export async function GET(req: NextRequest) {
  // Pass the same HS256 decoder that NextAuth uses to mint the session
  // cookie. Default getToken expects JWE — without overriding, it fails
  // to decode our HS256 cookie and returns null.
  const claims = await getToken({
    req,
    secret: process.env.NEXTAUTH_SECRET!,
    decode: jwtDecode,
  })
  if (!claims) return new Response('Unauthorized', { status: 401 })

  const token = jwt.sign(
    {
      sub: claims.sub,
      github_id: (claims as any).github_id,
      github_login: (claims as any).github_login,
      name: claims.name,
      email: claims.email,
      avatar_url: (claims as any).avatar_url,
    },
    process.env.NEXTAUTH_SECRET!,
    { algorithm: 'HS256', expiresIn: BACKEND_TOKEN_TTL_SECONDS },
  )

  return Response.json({
    token,
    expiresAt: Math.floor(Date.now() / 1000) + BACKEND_TOKEN_TTL_SECONDS,
  })
}
