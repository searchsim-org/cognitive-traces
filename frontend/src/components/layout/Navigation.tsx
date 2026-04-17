'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Github } from 'lucide-react'
import { Button } from '@/components/ui/button'
import Image from 'next/image'
import { useSession } from 'next-auth/react'
import { SignInButton } from '@/components/auth/SignInButton'
import { UserMenu } from '@/components/auth/UserMenu'

export function Navigation() {
  const pathname = usePathname()
  const { status } = useSession()

  const links = [
    { href: '/', label: 'Home' },
    { href: '/annotator', label: 'Annotator' },
    { href: '/datasets', label: 'Datasets' },
  ]

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-gray-200 bg-white/95 backdrop-blur-sm">
      <div className="container">
        <div className="flex h-20 items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <Image
              src="/images/logo.png"
              alt="Cognitive Traces Logo"
              width={38}
              height={38}
              className="group-hover:scale-105 transition-transform"
            />
            <span className="text-3xl font-bold text-gray-900">
              Traces
            </span>
          </Link>

          {/* Nav Links */}
          <div className="hidden md:flex items-center gap-8">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`text-sm font-semibold uppercase tracking-wider transition-colors ${pathname === link.href
                    ? 'text-gray-900'
                    : 'text-gray-500 hover:text-gray-900'
                  }`}
              >
                {link.label}
              </Link>
            ))}
          </div>

          {/* Right side: GitHub repo link + auth UI */}
          <div className="flex items-center gap-3">
            <Button
              asChild
              size="sm"
              variant="outline"
              className="rounded-full px-4"
            >
              <a
                href="https://github.com/searchsim-org/cognitive-traces"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2"
              >
                <Github className="w-4 h-4" />
                <span className="hidden sm:inline">GitHub</span>
              </a>
            </Button>
            {status === 'authenticated' ? <UserMenu /> : <SignInButton />}
          </div>
        </div>
      </div>
    </nav>
  )
}

