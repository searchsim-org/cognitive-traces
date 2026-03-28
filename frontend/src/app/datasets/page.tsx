'use client'

import { Navigation } from '@/components/layout/Navigation'
import { Footer } from '@/components/layout/Footer'
import { Search, MessageSquare, Film, ArrowRight, Download, ExternalLink } from 'lucide-react'
import { Button } from '@/components/ui/button'
import Link from 'next/link'

const datasets = [
  {
    name: 'AOL Search Sessions',
    description: 'Web search logs with archived pages, annotated with cognitive trace labels grounded in Information Foraging Theory.',
    sessions: '22,039',
    events: '245,786',
    icon: Search,
    bgColor: 'bg-blue-600',
    textColor: 'text-blue-600',
    huggingface: 'https://huggingface.co/datasets/searchsim/cognitive-traces-aol',
  },
  {
    name: 'Stack Overflow Q&A',
    description: 'Technical Q&A interactions capturing how developers search, browse, and resolve programming questions.',
    sessions: '18,629',
    events: '175,326',
    icon: MessageSquare,
    bgColor: 'bg-orange-600',
    textColor: 'text-orange-600',
    huggingface: 'https://huggingface.co/datasets/searchsim/cognitive-traces-stackoverflow',
  },
  {
    name: 'MovieLens Ratings',
    description: 'Movie rating preferences capturing how users explore, evaluate, and select entertainment content.',
    sessions: '10,274',
    events: '111,561',
    icon: Film,
    bgColor: 'bg-purple-600',
    textColor: 'text-purple-600',
    huggingface: 'https://huggingface.co/datasets/searchsim/cognitive-traces-movielens',
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
              Three diverse information-seeking domains with 532K+ cognitive trace labels across 50,942 sessions
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
                <h3 className="text-2xl font-bold text-gray-900 mb-1">{dataset.name}</h3>
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
                    <span className="text-sm text-gray-500">Events</span>
                    <span className={`text-xl font-bold ${dataset.textColor}`}>
                      {dataset.events}
                    </span>
                  </div>
                </div>

                {/* HuggingFace Link */}
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <a
                    href={dataset.huggingface}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`inline-flex items-center text-sm font-medium ${dataset.textColor} hover:underline`}
                  >
                    View on HuggingFace
                    <ExternalLink className="ml-1.5 w-3.5 h-3.5" />
                  </a>
                </div>
              </div>
            ))}

            {/* Request a dataset card */}
            <div className="group p-10 rounded-3xl border-2 border-dashed border-gray-300 hover:border-gray-400 transition-all bg-white flex flex-col justify-between">
              <div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">Request a Dataset</h3>
                <p className="text-gray-600 mb-8 leading-relaxed">
                  Don't see the dataset you need? Open a request and tell us about your use case.
                </p>
              </div>
              <div>
                <a
                  href="https://github.com/searchsim-org/cognitive-traces/issues/new"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center justify-center px-12 py-3 rounded-full bg-gray-900 text-white hover:bg-gray-800 text-lg font-medium"
                >
                  Request
                  <ArrowRight className="ml-2 w-5 h-5" />
                </a>
              </div>
            </div>
          </div>

          {/* Quick Start Section */}
          <div className="max-w-3xl mx-auto mb-20">
            <div className="p-8 rounded-2xl bg-gray-50 border border-gray-200">
              <h3 className="text-lg font-bold text-gray-900 mb-4">Quick Start</h3>
              <pre className="bg-gray-900 text-gray-100 rounded-xl p-6 text-sm overflow-x-auto">
                <code>{`from datasets import load_dataset

# Load any dataset directly
aol = load_dataset("searchsim/cognitive-traces-aol")
stackoverflow = load_dataset("searchsim/cognitive-traces-stackoverflow")
movielens = load_dataset("searchsim/cognitive-traces-movielens")

# Access as pandas DataFrame
df = aol["train"].to_pandas()`}</code>
              </pre>
            </div>
          </div>

          {/* CTA Section */}
          <div className="text-center space-y-6 max-w-3xl mx-auto">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gray-100 mb-4">
              <Download className="w-8 h-8 text-gray-900" />
            </div>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900">
              Browse All Datasets
            </h2>
            <p className="text-lg text-gray-600">
              Access all datasets with full annotations on HuggingFace
            </p>
            <div className="pt-4">
              <Button
                size="lg"
                className="bg-gray-900 hover:bg-gray-800 text-white rounded-full px-12 py-6 text-lg"
                asChild
              >
                <a
                  href="https://huggingface.co/searchsim"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center"
                >
                  View on HuggingFace
                  <ExternalLink className="ml-2 w-5 h-5" />
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
