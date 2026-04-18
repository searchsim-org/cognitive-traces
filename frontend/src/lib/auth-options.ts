import { type NextAuthOptions } from 'next-auth'
import GitHubProvider from 'next-auth/providers/github'
import jwt from 'jsonwebtoken'

const COOKIE_TOKEN_TTL_SECONDS = 60 * 60 * 24 * 30 // 30 days

// Exported so the same encode/decode functions can be reused by
// `getToken({ ..., encode, decode })` calls outside of NextAuth's own flow
// (e.g. our /api/auth/backend-token route). Keeping them in lockstep with
// what NextAuth's own session cookie uses is critical: the default getToken
// decoder expects JWE, but we sign HS256 JWS — mismatched decoders return
// null and silently log the user out at the API boundary.
export const jwtEncode: NextAuthOptions['jwt'] extends infer J
  ? J extends { encode?: infer E } ? E : never : never =
  // jsonwebtoken does not auto-populate `exp` for object payloads, so we
  // pass `expiresIn` explicitly. NextAuth strips any pre-set `exp` from
  // the payload before calling encode, so this is safe.
  async ({ token, secret }) =>
    jwt.sign({ ...(token ?? {}) }, secret as string, {
      algorithm: 'HS256',
      expiresIn: COOKIE_TOKEN_TTL_SECONDS,
    })

export const jwtDecode: NextAuthOptions['jwt'] extends infer J
  ? J extends { decode?: infer D } ? D : never : never =
  async ({ token, secret }) => {
    if (!token) return null
    return jwt.verify(token, secret as string, { algorithms: ['HS256'] }) as any
  }

export const authOptions: NextAuthOptions = {
  providers: [
    GitHubProvider({
      clientId: process.env.GITHUB_CLIENT_ID!,
      clientSecret: process.env.GITHUB_CLIENT_SECRET!,
    }),
  ],
  session: { strategy: 'jwt', maxAge: COOKIE_TOKEN_TTL_SECONDS },
  jwt: {
    encode: jwtEncode,
    decode: jwtDecode,
  },
  callbacks: {
    async jwt({ token, profile, account }) {
      if (profile && account?.provider === 'github') {
        // GitHub profile fields. Use `any` because the next-auth Profile
        // type doesn't surface GitHub-specific fields by default.
        const p = profile as any
        token.github_id = p.id
        token.github_login = p.login
        token.avatar_url = p.avatar_url
        token.name = p.name ?? token.name
        token.email = p.email ?? token.email
      }
      return token
    },
  },
}
