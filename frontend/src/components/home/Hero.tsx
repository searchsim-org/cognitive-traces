'use client'

import Link from 'next/link'
import { ArrowRight, Brain, Zap, Users } from 'lucide-react'

export function Hero() {
  return (
    <div className="relative overflow-hidden bg-gradient-to-br from-primary-50 to-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 md:py-32">
        <div className="text-center">
          <div className="flex justify-center mb-8">
            <Brain className="w-20 h-20 text-primary-600" />
          </div>
          
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6 animate-fade-in">
            Inferred Cognitive Traces
          </h1>
          
          <p className="text-xl md:text-2xl text-gray-600 mb-8 max-w-3xl mx-auto animate-slide-up">
            A general and reproducible framework for adding a layer of inferred cognitive traces
            to existing records of user behavior
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
            <Link href="/annotator" className="btn-primary text-lg px-8 py-3 flex items-center space-x-2">
              <span>Try Annotator Tool</span>
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link href="/datasets" className="btn-secondary text-lg px-8 py-3">
              Explore Datasets
            </Link>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <div className="flex flex-col items-center">
              <Zap className="w-10 h-10 text-primary-600 mb-3" />
              <h3 className="font-semibold text-gray-900 mb-2">Multi-Agent AI</h3>
              <p className="text-sm text-gray-600">
                Claude 3.5 Sonnet & GPT-4o working together for accurate annotations
              </p>
            </div>
            
            <div className="flex flex-col items-center">
              <Brain className="w-10 h-10 text-primary-600 mb-3" />
              <h3 className="font-semibold text-gray-900 mb-2">Theory-Grounded</h3>
              <p className="text-sm text-gray-600">
                Based on Information Foraging Theory principles
              </p>
            </div>
            
            <div className="flex flex-col items-center">
              <Users className="w-10 h-10 text-primary-600 mb-3" />
              <h3 className="font-semibold text-gray-900 mb-2">Human-in-the-Loop</h3>
              <p className="text-sm text-gray-600">
                Active learning with expert validation for quality assurance
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

