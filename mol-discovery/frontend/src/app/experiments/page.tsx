'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { experiment } from '@/services/api'

export default function ExperimentLogger() {
  const [experiments, setExperiments] = useState<any[]>([])
  const [formData, setFormData] = useState({
    molecule_id: '',
    activity: '',
    selectivity: '',
    stability: '',
    notes: ''
  })
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setError('')
      await experiment.log([formData])
      setSuccess(true)
      setExperiments([...experiments, { ...formData, timestamp: new Date().toISOString() }])
      setFormData({
        molecule_id: '',
        activity: '',
        selectivity: '',
        stability: '',
        notes: ''
      })
      setTimeout(() => setSuccess(false), 3000)
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to log experiment')
    }
  }

  return (
    <div className="container mx-auto py-12 px-4">
      <h1 className="text-4xl font-bold mb-8">Experiment Logger</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
          <h2 className="text-2xl font-bold mb-6">Log New Experiment</h2>
          
          {success && (
            <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
              Experiment logged successfully!
            </div>
          )}
          
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block mb-2 font-medium">Molecule ID</label>
              <input
                type="text"
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                value={formData.molecule_id}
                onChange={(e) => setFormData({...formData, molecule_id: e.target.value})}
                required
              />
            </div>
            
            <div>
              <label className="block mb-2 font-medium">Activity</label>
              <input
                type="number"
                step="0.01"
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                value={formData.activity}
                onChange={(e) => setFormData({...formData, activity: e.target.value})}
                required
              />
            </div>
            
            <div>
              <label className="block mb-2 font-medium">Selectivity</label>
              <input
                type="number"
                step="0.01"
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                value={formData.selectivity}
                onChange={(e) => setFormData({...formData, selectivity: e.target.value})}
                required
              />
            </div>
            
            <div>
              <label className="block mb-2 font-medium">Stability (hours)</label>
              <input
                type="number"
                step="0.1"
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                value={formData.stability}
                onChange={(e) => setFormData({...formData, stability: e.target.value})}
                required
              />
            </div>
            
            <div>
              <label className="block mb-2 font-medium">Notes</label>
              <textarea
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 h-24"
                value={formData.notes}
                onChange={(e) => setFormData({...formData, notes: e.target.value})}
              />
            </div>
            
            <Button type="submit" className="w-full">
              Log Experiment
            </Button>
          </form>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
          <h2 className="text-2xl font-bold mb-6">Recent Experiments</h2>
          {experiments.length === 0 ? (
            <p className="text-gray-500">No experiments logged yet</p>
          ) : (
            <div className="space-y-4">
              {experiments.map((exp, idx) => (
                <div key={idx} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                  <p className="font-semibold">{exp.molecule_id}</p>
                  <div className="grid grid-cols-3 gap-2 mt-2 text-sm">
                    <div>Activity: {exp.activity}</div>
                    <div>Selectivity: {exp.selectivity}</div>
                    <div>Stability: {exp.stability}h</div>
                  </div>
                  {exp.notes && <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">{exp.notes}</p>}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
