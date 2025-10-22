'use client'

import { Navigation } from '@/components/layout/Navigation'
import { DatasetCard } from '@/components/datasets/DatasetCard'
import { Download, Search, MessageSquare, Film } from 'lucide-react'

const datasets = [
  {
    name: 'AOL-IA',
    domain: 'Web Search',
    sessions: '500K',
    events: '3.1M',
    labels: '3.1M',
    description: 'Large-scale log of user queries and clicks with archived web page content from Internet Archive',
    icon: Search,
    color: 'blue',
  },
  {
    name: 'Stack Overflow',
    domain: 'Technical Q&A',
    sessions: '2.1M Users',
    events: '16.4M',
    labels: '16.4M',
    description: 'Complete history of questions, answers, comments, and votes with cognitive annotations',
    icon: MessageSquare,
    color: 'orange',
  },
  {
    name: 'MovieLens-25M',
    domain: 'Recommendations',
    sessions: '162K Users',
    events: '25M',
    labels: '25M',
    description: 'Movie ratings and tags with inferred cognitive states related to preference formation',
    icon: Film,
    color: 'purple',
  },
]

export default function DatasetsPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Annotated Datasets
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Explore our collection of cognitively annotated datasets spanning multiple information-seeking domains
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-12">
          {datasets.map((dataset) => (
            <DatasetCard key={dataset.name} dataset={dataset} />
          ))}
        </div>

        <div className="card text-center">
          <Download className="w-12 h-12 mx-auto mb-4 text-primary-600" />
          <h3 className="text-xl font-semibold mb-2">Download Complete Collection</h3>
          <p className="text-gray-600 mb-4">
            Access all datasets with full annotations in CSV and JSON formats
          </p>
          <a
            href="https://github.com/searchsim-org/cognitive-traces"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary inline-block"
          >
            View on GitHub
          </a>
        </div>
      </div>
    </div>
  )
}

