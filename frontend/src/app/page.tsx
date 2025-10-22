import { Hero } from '@/components/home/Hero'
import { Features } from '@/components/home/Features'
import { Statistics } from '@/components/home/Statistics'
import { GetStarted } from '@/components/home/GetStarted'
import { Navigation } from '@/components/layout/Navigation'
import { Footer } from '@/components/layout/Footer'

export default function Home() {
  return (
    <div className="min-h-screen">
      <Navigation />
      <main>
        <Hero />
        <Features />
        <Statistics />
        <GetStarted />
      </main>
      <Footer />
    </div>
  )
}

