import { Brain, Github, Mail } from 'lucide-react'

export function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <Brain className="w-6 h-6 text-primary-400" />
              <span className="text-lg font-bold text-white">
                Cognitive Traces
              </span>
            </div>
            <p className="text-sm">
              A general and reproducible framework for adding inferred cognitive traces to user behavior logs.
            </p>
          </div>
          
          <div>
            <h3 className="text-white font-semibold mb-4">Resources</h3>
            <ul className="space-y-2 text-sm">
              <li><a href="#" className="hover:text-white transition-colors">Documentation</a></li>
              <li><a href="#" className="hover:text-white transition-colors">API Reference</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Research Paper</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Citation</a></li>
            </ul>
          </div>
          
          <div>
            <h3 className="text-white font-semibold mb-4">Connect</h3>
            <div className="flex space-x-4">
              <a href="https://github.com/searchsim-org/cognitive-traces" 
                 className="hover:text-white transition-colors"
                 target="_blank"
                 rel="noopener noreferrer">
                <Github className="w-6 h-6" />
              </a>
              <a href="mailto:contact@example.com" className="hover:text-white transition-colors">
                <Mail className="w-6 h-6" />
              </a>
            </div>
          </div>
        </div>
        
        <div className="border-t border-gray-800 mt-8 pt-8 text-sm text-center">
          <p>&copy; 2025 Cognitive Traces Project. Released under MIT License.</p>
        </div>
      </div>
    </footer>
  )
}

