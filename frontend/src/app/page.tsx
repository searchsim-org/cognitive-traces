import { Hero } from '@/components/home/Hero'
import { Features } from '@/components/home/Features'
import { Navigation } from '@/components/layout/Navigation'
import { Footer } from '@/components/layout/Footer'

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col bg-white">
      <Navigation />
      <main className="flex-1">
        <Hero />
        <Features />
      </main>
      <Footer />
    </div>
  )
}

