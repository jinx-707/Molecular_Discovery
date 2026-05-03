'use client'

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { model } from '@/services/api'

export default function ModelHealth() {
  const [health, setHealth] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [retraining, setRetraining] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchHealth()
  }, [])

  const fetchHealth = async () => {
    try {
      setLoading(true)
      setError('')
      const response = await model.health()
      setHealth(response.data)
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch model health')
    } finally {
      setLoading(false)
    }
  }

  const handleRetrain = async () => {
    try {
      setRetraining(true)
      setError('')
      await model.retrain()
      alert('Retraining started successfully!')
      fetchHealth()
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to start retraining')
    } finally {
      setRetraining(false)
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto py-12 px-4">
        <div className="flex justify-center items-center h-64">
          <div className="text-xl">Loading model health...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-12 px-4">
      <h1 className="text-4xl font-bold mb-8">Model Health Dashboard</h1>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-2">Catalyst Predictor</h3>
          <div className="text-3xl font-bold text-green-600">
            {health?.catalyst_predictor?.status || 'Unknown'}
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
            Accuracy: {health?.catalyst_predictor?.accuracy || 'N/A'}
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-2">Enzyme Predictor</h3>
          <div className="text-3xl font-bold text-green-600">
            {health?.enzyme_predictor?.status || 'Unknown'}
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
            Accuracy: {health?.enzyme_predictor?.accuracy || 'N/A'}
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-2">Generator Models</h3>
          <div className="text-3xl font-bold text-green-600">
            {health?.generator?.status || 'Unknown'}
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
            Last updated: {health?.generator?.last_updated || 'N/A'}
          </p>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
        <h2 className="text-2xl font-bold mb-4">Model Management</h2>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          Retrain models with the latest experimental data to improve predictions.
        </p>
        <Button 
          onClick={handleRetrain} 
          disabled={retraining}
          size="lg"
        >
          {retraining ? 'Starting Retraining...' : 'Start Retraining'}
        </Button>
      </div>

      <div className="mt-8 bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
        <h2 className="text-2xl font-bold mb-4">Performance Metrics</h2>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between mb-2">
              <span>Prediction Accuracy</span>
              <span className="font-semibold">85%</span>
            </div>
            <div className="bg-gray-200 dark:bg-gray-700 h-3 rounded-full">
              <div className="bg-blue-500 h-3 rounded-full" style={{width: '85%'}}></div>
            </div>
          </div>
          
          <div>
            <div className="flex justify-between mb-2">
              <span>Model Confidence</span>
              <span className="font-semibold">92%</span>
            </div>
            <div className="bg-gray-200 dark:bg-gray-700 h-3 rounded-full">
              <div className="bg-green-500 h-3 rounded-full" style={{width: '92%'}}></div>
            </div>
          </div>
          
          <div>
            <div className="flex justify-between mb-2">
              <span>Training Data Coverage</span>
              <span className="font-semibold">78%</span>
            </div>
            <div className="bg-gray-200 dark:bg-gray-700 h-3 rounded-full">
              <div className="bg-purple-500 h-3 rounded-full" style={{width: '78%'}}></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
