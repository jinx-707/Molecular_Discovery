'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { discovery } from '@/services/api'
import ResultsTable from '@/components/ResultsTable'

export default function DiscoveryWizard() {
  const [step, setStep] = useState(1)
  const [reaction, setReaction] = useState('')
  const [constraints, setConstraints] = useState<any>({})
  const [runId, setRunId] = useState('')
  const [status, setStatus] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const nextStep = () => setStep(step + 1)
  const prevStep = () => setStep(step - 1)

  const handleSubmit = async () => {
    try {
      setLoading(true)
      setError('')
      const response = await discovery.start({ reaction, type: 'catalyst', constraints })
      setRunId(response.data.run_id)
      setStep(4)
      pollStatus(response.data.run_id)
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to start discovery')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const pollStatus = async (id: string) => {
    const interval = setInterval(async () => {
      try {
        const statusRes = await discovery.status(id)
        setStatus(statusRes.data.status)
        if (statusRes.data.status === 'completed') {
          clearInterval(interval)
          const resultsRes = await discovery.results(id)
          setResults(resultsRes.data.candidates)
        } else if (statusRes.data.status === 'failed') {
          clearInterval(interval)
          setError('Discovery failed')
        }
      } catch (err) {
        console.error('Polling error:', err)
      }
    }, 2000)
  }

  return (
    <div className="container mx-auto py-12 px-4">
      <div className="max-w-2xl mx-auto">
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {step === 1 && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
            <h2 className="text-3xl font-bold mb-8">Step 1: Define Reaction</h2>
            <textarea
              className="w-full p-4 border border-gray-300 dark:border-gray-600 rounded-lg h-32 resize-vertical bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="e.g. CO2 + 3 H2 → CH3OH + H2O or CO oxidation on Pt"
              value={reaction}
              onChange={(e) => setReaction(e.target.value)}
            />
            <Button onClick={nextStep} className="mt-4" disabled={!reaction}>
              Next
            </Button>
          </div>
        )}
        
        {step === 2 && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
            <h2 className="text-3xl font-bold mb-8">Step 2: Constraints</h2>
            <div className="space-y-6">
              <div>
                <label className="block mb-2 font-medium">
                  Min Stability (h): {constraints.stability || 1}
                </label>
                <input 
                  type="range" 
                  min="1" 
                  max="100" 
                  className="w-full" 
                  value={constraints.stability || 1}
                  onChange={(e) => setConstraints({...constraints, stability: e.target.value})} 
                />
              </div>
              <div>
                <label className="block mb-2 font-medium">
                  Temperature (°C): {constraints.temp || 25}
                </label>
                <input 
                  type="range" 
                  min="25" 
                  max="500" 
                  className="w-full" 
                  value={constraints.temp || 25}
                  onChange={(e) => setConstraints({...constraints, temp: e.target.value})} 
                />
              </div>
            </div>
            <div className="flex gap-4 mt-8">
              <Button variant="outline" onClick={prevStep}>
                Back
              </Button>
              <Button onClick={handleSubmit} disabled={loading}>
                {loading ? 'Starting...' : 'Start Discovery'}
              </Button>
            </div>
          </div>
        )}
        
        {step === 4 && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
            <h2 className="text-3xl font-bold mb-8">Discovery Progress</h2>
            <div className="bg-gray-200 dark:bg-gray-700 h-4 rounded-full mb-4">
              <div 
                className="bg-blue-500 h-4 rounded-full transition-all duration-500" 
                style={{width: status === 'completed' ? '100%' : '60%'}}
              ></div>
            </div>
            <p className="mb-4 text-lg">Status: <span className="font-semibold">{status || 'Starting...'}</span></p>
            {results.length > 0 && (
              <div className="mt-8">
                <h3 className="text-2xl font-bold mb-4">Results</h3>
                <ResultsTable data={results} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
