import { Github, Mail, Twitter } from 'lucide-react'
import Link from 'next/link'
import Image from 'next/image'

export function Footer() {
  return (
    <footer className="relative border-t border-gray-200 bg-white">
      <div className="container py-8 md:py-10">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-12 mb-6">
          {/* Brand */}
          <div className="md:col-span-4 space-y-4">
            <Link href="/" className="flex items-center gap-3 group w-fit">
              <Image 
                src="/images/logo.png" 
                alt="Cognitive Traces Logo" 
                width={40} 
                height={40}
                className="group-hover:scale-105 transition-transform"
              />
              <span className="text-3xl font-bold text-gray-900">
                Traces
              </span>
            </Link>
            <p className="text-gray-600 leading-relaxed max-w-sm">
              Transform user behavior into cognitive insights with multi-agent AI and Information Foraging Theory.
            </p>
            
          </div>
          
          {/* Resources */}
          <div className="md:col-span-3">
            <h3 className="font-bold text-gray-900 mb-4 uppercase">Resources</h3>
            <ul className="space-y-3">
              {[
                { label: 'Documentation', href: '#' },
                { label: 'Research Paper', href: '#' },
              ].map((link) => (
                <li key={link.label}>
                  <Link 
                    href={link.href} 
                    className="text-gray-600 hover:text-gray-900 transition-colors inline-flex items-center group"
                  >
                    {link.label}
                    <span className="opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all ml-1">→</span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
          
          {/* Product */}
          <div className="md:col-span-2">
            <h3 className="font-bold text-gray-900 mb-4 uppercase">Product</h3>
            <ul className="space-y-3">
              {[
                { label: 'Annotator', href: '/annotator' },
                { label: 'Datasets', href: '/datasets' },
              ].map((link) => (
                <li key={link.label}>
                  <Link 
                    href={link.href} 
                    className="text-gray-600 hover:text-gray-900 transition-colors inline-flex items-center group"
                  >
                    {link.label}
                    <span className="opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all ml-1">→</span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
          
          {/* Legal */}
          <div className="md:col-span-3">
            <h3 className="font-bold text-gray-900 mb-4 uppercase">Social</h3>
            {/* Social Links */}
            <div className="flex gap-3 pt-2">
              <a 
                href="https://github.com/searchsim-org/cognitive-traces" 
                className="w-10 h-10 rounded-lg bg-gray-100 hover:bg-gray-900 flex items-center justify-center text-gray-600 hover:text-white transition-all"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="GitHub"
              >
                <Github className="w-5 h-5" />
              </a>
              <a 
                href="mailto:szerhoudi@acm.org" 
                className="w-10 h-10 rounded-lg bg-gray-100 hover:bg-gray-900 flex items-center justify-center text-gray-600 hover:text-white transition-all"
                aria-label="Email"
              >
                <Mail className="w-5 h-5" />
              </a>
            </div>
          </div>
        </div>
        
        {/* Bottom Bar */}
        <div className="pt-4 border-t border-gray-200">
          <div className="flex flex-col md:flex-row justify-end items-center gap-4">
            <p className="text-sm text-gray-600">
              © 2025 Cognitive Traces. All rights reserved.
            </p>
          </div>
        </div>
      </div>
    </footer>
  )
}

