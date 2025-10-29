import type { Metadata } from 'next'
import './globals.css'
import { Providers } from '@/components/Providers'
import { Toaster } from 'react-hot-toast'

export const metadata: Metadata = {
  title: 'Cognitive Traces - Interactive Annotation Tool',
  description: 'Multi-agent framework for annotating user behavior with cognitive traces based on Information Foraging Theory',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Product+Sans:wght@400;500;700&display=swap" rel="stylesheet" />
      </head>
      <body className="font-product-sans">
        <Providers>
          {children}
          <Toaster position="top-right" />
        </Providers>
      </body>
    </html>
  )
}

