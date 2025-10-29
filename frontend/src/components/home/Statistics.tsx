import { Search, MessageSquare, Film } from 'lucide-react'

const datasets = [
  { 
    name: 'AOL-IA',
    description: 'Web search logs with archived pages',
    sessions: '500K',
    labels: '3.1M',
    icon: Search,
    gradient: 'from-blue-600 to-cyan-600',
  },
  { 
    name: 'Stack Overflow',
    description: 'Technical Q&A interactions',
    sessions: '2.1M',
    labels: '16.4M',
    icon: MessageSquare,
    gradient: 'from-orange-600 to-red-600',
  },
  { 
    name: 'MovieLens-25M',
    description: 'Movie rating preferences',
    sessions: '162K',
    labels: '25M',
    icon: Film,
    gradient: 'from-purple-600 to-pink-600',
  },
]

export function Statistics() {
  return (
    <section className="relative py-24 md:py-32 bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-800">
      <div className="container">
        <div className="text-center mb-16 space-y-4">
          <h2 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-400 bg-clip-text text-transparent">
            Annotated Datasets
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-300">
            Three diverse information-seeking domains
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {datasets.map((dataset, index) => (
            <div 
              key={index}
              className="group relative p-8 rounded-3xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:scale-105 transition-all duration-300"
            >
              {/* Icon */}
              <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${dataset.gradient} p-4 mb-6 group-hover:scale-110 transition-transform duration-300`}>
                <dataset.icon className="w-full h-full text-white" />
              </div>
              
              {/* Content */}
              <h3 className="text-2xl font-bold mb-2 text-gray-900 dark:text-white">
                {dataset.name}
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                {dataset.description}
              </p>
              
              {/* Stats */}
              <div className="space-y-3 pt-4 border-t border-gray-200 dark:border-gray-700">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">Sessions</span>
                  <span className={`text-lg font-bold bg-gradient-to-r ${dataset.gradient} bg-clip-text text-transparent`}>
                    {dataset.sessions}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">Labels</span>
                  <span className={`text-lg font-bold bg-gradient-to-r ${dataset.gradient} bg-clip-text text-transparent`}>
                    {dataset.labels}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

