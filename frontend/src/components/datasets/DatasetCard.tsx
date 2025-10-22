import { LucideIcon } from 'lucide-react'

interface DatasetCardProps {
  dataset: {
    name: string
    domain: string
    sessions: string
    events: string
    labels: string
    description: string
    icon: LucideIcon
    color: string
  }
}

const colorMap: Record<string, string> = {
  blue: 'bg-blue-100 text-blue-600',
  orange: 'bg-orange-100 text-orange-600',
  purple: 'bg-purple-100 text-purple-600',
}

export function DatasetCard({ dataset }: DatasetCardProps) {
  const Icon = dataset.icon
  const colorClass = colorMap[dataset.color] || colorMap.blue
  
  return (
    <div className="card hover:shadow-lg transition-shadow duration-200">
      <div className={`w-12 h-12 rounded-lg ${colorClass} flex items-center justify-center mb-4`}>
        <Icon className="w-6 h-6" />
      </div>
      
      <h3 className="text-2xl font-bold text-gray-900 mb-2">
        {dataset.name}
      </h3>
      
      <div className="inline-block bg-gray-100 text-gray-700 text-sm px-3 py-1 rounded-full mb-4">
        {dataset.domain}
      </div>
      
      <p className="text-gray-600 mb-6">
        {dataset.description}
      </p>
      
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-600">Sessions/Users:</span>
          <span className="font-semibold text-gray-900">{dataset.sessions}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Total Events:</span>
          <span className="font-semibold text-gray-900">{dataset.events}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Cognitive Labels:</span>
          <span className="font-semibold text-gray-900">{dataset.labels}</span>
        </div>
      </div>
    </div>
  )
}

