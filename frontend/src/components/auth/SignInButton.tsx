'use client'
import { signIn } from 'next-auth/react'
import { Github } from 'lucide-react'

export function SignInButton() {
  return (
    <button
      onClick={() => signIn('github')}
      className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gray-900 text-white hover:bg-gray-800 text-sm font-medium"
    >
      <Github className="w-4 h-4" /> Sign in with GitHub
    </button>
  )
}
