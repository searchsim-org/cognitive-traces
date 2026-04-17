import { getToken } from 'next-auth/jwt'
import jwt from 'jsonwebtoken'
import { NextRequest } from 'next/server'

const BACKEND_TOKEN_TTL_SECONDS = 60 * 15 // 15 minutes

export async function GET(req: NextRequest) {
  const claims = await getToken({ req, secret: process.env.NEXTAUTH_SECRET! })
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
