import { FileCode, Layers, Upload, Download } from 'lucide-react'

const features = [
  {
    icon: Layers,
    title: 'Multi-Agent Framework',
    description: 'Three specialized AI agents (Analyst, Critic, Judge) collaborate to ensure high-quality annotations with transparent reasoning.',
  },
  {
    icon: Upload,
    title: 'Flexible Data Ingestion',
    description: 'Upload session logs in CSV or JSON format. Supports AOL, Stack Overflow, MovieLens, and custom datasets.',
  },
  {
    icon: FileCode,
    title: 'Pre-Trained Model',
    description: 'Lightweight transformer model for fast cognitive label prediction. 73% F1-score on session abandonment prediction.',
  },
  {
    icon: Download,
    title: 'Easy Export',
    description: 'Export annotated data in analysis-ready formats with comprehensive metadata and justifications.',
  },
]

export function Features() {
  return (
    <div className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Powerful Features
          </h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Everything you need to annotate user behavior with cognitive traces
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {features.map((feature, index) => (
            <div key={index} className="card hover:shadow-lg transition-shadow duration-200">
              <feature.icon className="w-12 h-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {feature.title}
              </h3>
              <p className="text-gray-600">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

