'use client'

import Link from 'next/link'
import { Button } from "@/components/ui/button"

export default function Home() {
  return (
    <div className="container mx-auto py-12 px-4">
      <div className="text-center mb-16">
        <h1 className="text-6xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent mb-6">
          MolDiscovery
        </h1>
        <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto mb-12">
          AI-powered catalyst and enzyme discovery platform
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link href="/discovery">
            <Button size="lg" className="px-8">
              Start Discovery
            </Button>
          </Link>
          <Link href="/projects">
            <Button variant="outline" size="lg">
              View Recent Projects
            </Button>
          </Link>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 text-center">
          <div className="text-4xl mb-4">⚡</div>
          <h3 className="text-xl font-bold mb-2">Instant Prediction</h3>
          <p className="text-gray-600 dark:text-gray-300">AI models predict activity, selectivity, and stability in seconds</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 text-center">
          <div className="text-4xl mb-4">🔬</div>
          <h3 className="text-xl font-bold mb-2">Structure Validation</h3>
          <p className="text-gray-600 dark:text-gray-300">3D visualization and energy profiling for all candidates</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 text-center">
          <div className="text-4xl mb-4">📈</div>
          <h3 className="text-xl font-bold mb-2">Active Learning</h3>
          <p className="text-gray-600 dark:text-gray-300">Learn from your experiments and automatically improve</p>
        </div>
      </div>
    </div>
  )
}
