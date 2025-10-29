'use client'

import Link from 'next/link'
import { ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'

export function Hero() {
  return (
    <div className="relative bg-white">
      <div className="container">
        <div className="flex flex-col items-center text-center py-16 md:py-20 lg:py-32 space-y-12 max-w-4xl mx-auto">
          {/* Ultra minimal heading */}
          <div className="space-y-8">
            <h1 className="text-6xl md:text-7xl lg:text-8xl font-bold tracking-tight text-gray-900">
              Cognitive&nbsp;
              <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Traces
              </span>
            </h1>
            <p className="text-2xl md:text-3xl text-gray-600 font-light leading-relaxed">
              Uncover the cognitive patterns hidden in every user interaction
            </p>
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4">
            <Button size="lg" className="bg-gray-900 hover:bg-gray-800 text-white px-12 py-6 text-lg rounded-full" asChild>
              <Link href="/annotator">
                Get Started
                <ArrowRight className="ml-2 w-5 h-5" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" className="border-2 border-gray-300 hover:bg-gray-50 px-12 py-6 text-lg rounded-full" asChild>
              <Link href="/datasets">
                Explore Datasets
              </Link>
            </Button>
          </div>

          {/* Minimal stats */}
          <div className="flex flex-wrap justify-center gap-12 pt-8 text-md text-gray-500">
            <div>
              <span className="text-4xl font-bold text-gray-900">44.5M+&nbsp;</span> annotations
            </div>
            <div className="w-px bg-gray-200" />
            <div>
              <span className="text-4xl font-bold text-gray-900">3&nbsp;</span> datasets
            </div>
          </div>
        </div>
      </div>

      {/* Bottom fade */}
      <div className="absolute bottom-0 inset-x-0 h-24 bg-gradient-to-t from-gray-50 to-transparent" />
    </div>
  )
}