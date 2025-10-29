'use client'

import { Navigation } from '@/components/layout/Navigation'
import { Footer } from '@/components/layout/Footer'
import { Search, MessageSquare, Film, ArrowRight, Download } from 'lucide-react'
import { Button } from '@/components/ui/button'
import Link from 'next/link'

const datasets = [
  {
    name: 'AOL-IA',
    description: 'Web search logs with archived pages',
    sessions: '500K',
    labels: '3.1M',
    icon: Search,
    bgColor: 'bg-blue-600',
    textColor: 'text-blue-600',
  },
  {
    name: 'Stack Overflow',
    description: 'Technical Q&A interactions',
    sessions: '2.1M',
    labels: '16.4M',
    icon: MessageSquare,
    bgColor: 'bg-orange-600',
    textColor: 'text-orange-600',
  },
  {
    name: 'MovieLens-25M',
    description: 'Movie rating preferences',
    sessions: '162K',
    labels: '25M',
    icon: Film,
    bgColor: 'bg-purple-600',
    textColor: 'text-purple-600',
  },
]

export default function DatasetsPage() {
  return (
    <div className="min-h-screen flex flex-col bg-white">
      <Navigation />
      
      <main className="flex-1">
        {/* Hero Section */}
        <div className="container py-20 md:py-32">
          <div className="text-center mb-20 space-y-6 max-w-4xl mx-auto">
            <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight text-gray-900">
              Annotated Datasets
            </h1>
            <p className="text-xl md:text-2xl text-gray-600 font-light leading-relaxed">
              Three diverse information-seeking domains with 44.5M+ cognitive labels
            </p>
          </div>

          {/* Dataset Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-20 max-w-6xl mx-auto">
            {datasets.map((dataset, index) => (
              <div 
                key={index}
                className="group p-10 rounded-3xl border border-gray-200 hover:border-gray-300 transition-all bg-white"
              >
                {/* Icon */}
                <div className={`w-16 h-16 rounded-2xl ${dataset.bgColor} p-4 mb-6`}>
                  <dataset.icon className="w-full h-full text-white" />
                </div>
                
                {/* Content */}
                <h3 className="text-2xl font-bold mb-3 text-gray-900">
                  {dataset.name}
                </h3>
                <p className="text-gray-600 mb-8 leading-relaxed">
                  {dataset.description}
                </p>
                
                {/* Stats */}
                <div className="space-y-4 pt-6 border-t border-gray-200">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Sessions</span>
                    <span className={`text-xl font-bold ${dataset.textColor}`}>
                      {dataset.sessions}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Labels</span>
                    <span className={`text-xl font-bold ${dataset.textColor}`}>
                      {dataset.labels}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* CTA Section */}
          <div className="text-center space-y-6 max-w-3xl mx-auto">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gray-100 mb-4">
              <Download className="w-8 h-8 text-gray-900" />
            </div>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900">
              Download Complete Collection
            </h2>
            <p className="text-lg text-gray-600">
              Access all datasets with full annotations in CSV and JSON formats
            </p>
            <div className="pt-4">
              <Button 
                size="lg" 
                className="bg-gray-900 hover:bg-gray-800 text-white rounded-full px-12 py-6 text-lg"
                asChild
              >
                <a
                  href="https://github.com/searchsim-org/cognitive-traces"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center"
                >
                  View on GitHub
                  <ArrowRight className="ml-2 w-5 h-5" />
                </a>
              </Button>
            </div>
          </div>
        </div>
      </main>
      
      <Footer />
    </div>
  )
}

