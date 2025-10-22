import { BookOpen, Code, Database } from 'lucide-react'

const steps = [
  {
    icon: Database,
    title: 'Explore Datasets',
    description: 'Browse our annotated collections spanning AOL, Stack Overflow, and MovieLens',
    link: '/datasets',
  },
  {
    icon: Code,
    title: 'Use the Annotator',
    description: 'Upload your own session logs and generate cognitive annotations with AI assistance',
    link: '/annotator',
  },
  {
    icon: BookOpen,
    title: 'Read the Docs',
    description: 'Learn about the multi-agent framework, IFT schema, and integration options',
    link: 'https://github.com/searchsim-org/cognitive-traces',
  },
]

export function GetStarted() {
  return (
    <div className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Get Started
          </h2>
          <p className="text-xl text-gray-600">
            Three ways to use Cognitive Traces
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {steps.map((step, index) => (
            <a
              key={index}
              href={step.link}
              className="card hover:shadow-lg transition-all duration-200 hover:-translate-y-1 cursor-pointer group"
            >
              <div className="flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-4 group-hover:bg-primary-200 transition-colors">
                <step.icon className="w-8 h-8 text-primary-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {step.title}
              </h3>
              <p className="text-gray-600">
                {step.description}
              </p>
            </a>
          ))}
        </div>
      </div>
    </div>
  )
}

