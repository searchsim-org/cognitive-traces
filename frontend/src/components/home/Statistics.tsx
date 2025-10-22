const stats = [
  { value: '44.5M+', label: 'Cognitive Labels', description: 'Across all datasets' },
  { value: '3', label: 'Domains', description: 'Web Search, Q&A, Recommendations' },
  { value: '6', label: 'IFT Labels', description: 'Based on Information Foraging Theory' },
  { value: '0.78', label: 'Inter-Annotator Agreement', description: 'Krippendorff\'s α' },
]

export function Statistics() {
  return (
    <div className="py-20 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            By the Numbers
          </h2>
          <p className="text-xl text-gray-600">
            Large-scale, validated cognitive annotations
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {stats.map((stat, index) => (
            <div key={index} className="text-center">
              <div className="text-5xl font-bold text-primary-600 mb-2">
                {stat.value}
              </div>
              <div className="text-xl font-semibold text-gray-900 mb-1">
                {stat.label}
              </div>
              <div className="text-sm text-gray-600">
                {stat.description}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

