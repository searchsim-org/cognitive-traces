import { Layers, Upload, Zap, Users } from 'lucide-react'

const features = [
  {
    icon: Layers,
    title: 'Multi-Agent Framework',
    description: 'Three specialized AI agents collaborate to produce high-quality annotations with transparent reasoning.',
    bgColor: 'bg-blue-500',
  },
  {
    icon: Upload,
    title: 'Flexible Data Ingestion',
    description: 'Upload session logs in CSV or JSON format. Works with any behavioral dataset.',
    bgColor: 'bg-purple-500',
  },
  // {
  //   icon: Zap,
  //   title: 'Pre-Trained Model',
  //   description: 'Fast cognitive label prediction with 73% F1-score on session abandonment.',
  //   bgColor: 'bg-amber-500',
  // },
  {
    icon: Users,
    title: 'Human-in-the-Loop',
    description: 'Active learning flags uncertain cases for expert review and validation.',
    bgColor: 'bg-green-500',
  },
]

export function Features() {
  return (
    <section className="relative py-20 md:py-32 bg-white">
      <div className="container">
        <div className="text-center mb-20 space-y-6 max-w-4xl mx-auto">
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold tracking-tight text-gray-900">
            Why Cognitive Traces?
          </h2>
          <p className="text-lg md:text-xl text-gray-600 font-light leading-relaxed">
            Everything you need to enrich behavioral data with cognitive insights
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {features.map((feature, index) => (
            <div 
              key={index}
              className="p-10 rounded-3xl border border-gray-200 hover:border-gray-300 transition-all bg-white"
            >
              {/* Icon */}
              <div className={`w-16 h-16 rounded-2xl ${feature.bgColor} p-4 mb-6`}>
                <feature.icon className="w-full h-full text-white" />
              </div>
              
              {/* Content */}
              <h3 className="text-2xl font-bold mb-3 text-gray-900">
                {feature.title}
              </h3>
              <p className="text-gray-600 leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

