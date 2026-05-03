'use client'

import React, { useState, useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { api } from '@/services/api'

interface ExperimentEntry {
  candidate_id: string
  candidate_name: string
  activity: string
  selectivity: string
  stability: string
  temperature: string
  pressure: string
  researcher: string
}

interface LoggedResult {
  experiment_id: string
  discrepancy: number
  needs_retraining?: boolean
}

function ExperimentsContent() {
  const params = useSearchParams()
  const prefillId   = params.get('candidate_id') || ''
  const prefillName = params.get('name') || ''

  const [form, setForm] = useState<ExperimentEntry>({
    candidate_id:   prefillId,
    candidate_name: prefillName,
    activity:       '',
    selectivity:    '',
    stability:      '',
    temperature:    '350',
    pressure:       '1',
    researcher:     '',
  })
  const [csvFile, setCsvFile]     = useState<File | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess]     = useState<LoggedResult | null>(null)
  const [error, setError]         = useState('')
  const [history, setHistory]     = useState<LoggedResult[]>([])

  // Update form if URL params change (e.g. navigating from discovery page)
  useEffect(() => {
    if (prefillId) setForm(f => ({ ...f, candidate_id: prefillId, candidate_name: prefillName }))
  }, [prefillId, prefillName])

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.candidate_id || !form.activity) {
      setError('Candidate ID and Activity are required.')
      return
    }
    setSubmitting(true)
    setError('')
    setSuccess(null)
    try {
      const res = await api.logExperiment({
        candidate_id: form.candidate_id,
        activity:     parseFloat(form.activity),
        selectivity:  form.selectivity ? parseFloat(form.selectivity) : undefined,
        stability:    form.stability   ? parseInt(form.stability)     : undefined,
        temperature:  parseFloat(form.temperature),
        pressure:     parseFloat(form.pressure),
        researcher:   form.researcher || 'unknown',
      })
      const result: LoggedResult = {
        experiment_id:   res.experiment_id || '',
        discrepancy:     res.discrepancy   || 0,
        needs_retraining: (res.discrepancy || 0) > 0.2,
      }
      setSuccess(result)
      setHistory(h => [result, ...h])
      setForm(f => ({ ...f, activity: '', selectivity: '', stability: '' }))
    } catch (e: any) {
      setError(e.message || 'Failed to log experiment')
    } finally {
      setSubmitting(false)
    }
  }

  const handleCsvUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!csvFile) { setError('Select a CSV file first.'); return }
    setSubmitting(true)
    setError('')
    setSuccess(null)
    try {
      const res = await api.logExperimentCSV(csvFile)
      setSuccess({
        experiment_id:   `${res.experiments_logged} experiments`,
        discrepancy:     0,
        needs_retraining: false,
      })
      setCsvFile(null)
    } catch (e: any) {
      setError(e.message || 'CSV upload failed')
    } finally {
      setSubmitting(false)
    }
  }

  const discrepancyColor = (d: number) =>
    d > 0.3 ? 'text-red-600' : d > 0.15 ? 'text-yellow-600' : 'text-green-600'

  return (
    <div className="max-w-6xl mx-auto py-10 px-4 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Experiment Logger</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Log lab results to compare with AI predictions and improve the model.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ── Manual entry ── */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6">
          <h2 className="text-xl font-bold mb-5 text-gray-900 dark:text-white">Log Single Result</h2>

          {success && (
            <div className="mb-4 bg-green-50 dark:bg-green-900/30 border border-green-300
                            dark:border-green-700 rounded-lg p-4 text-sm">
              <div className="font-semibold text-green-800 dark:text-green-200">
                Logged: {success.experiment_id}
              </div>
              <div className={`mt-1 ${discrepancyColor(success.discrepancy)}`}>
                Discrepancy vs prediction: {(success.discrepancy * 100).toFixed(1)}%
                {success.needs_retraining && (
                  <span className="ml-2 font-semibold">&mdash; retraining recommended</span>
                )}
              </div>
            </div>
          )}

          {error && (
            <div className="mb-4 bg-red-50 dark:bg-red-900/30 border border-red-300
                            dark:border-red-700 rounded-lg p-3 text-sm text-red-700 dark:text-red-300">
              {error}
            </div>
          )}

          <form onSubmit={handleFormSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="sm:col-span-2">
                <label className="block text-sm font-semibold mb-1 text-gray-700 dark:text-gray-300">
                  Candidate ID *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. zsm-5-ga-001 or UUID from discovery"
                  className="w-full p-2.5 border border-gray-300 dark:border-gray-600 rounded-lg
                             bg-white dark:bg-gray-700 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  value={form.candidate_id}
                  onChange={e => setForm(f => ({ ...f, candidate_id: e.target.value }))}
                />
                {form.candidate_name && (
                  <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">{form.candidate_name}</p>
                )}
              </div>

              {[
                { key: 'activity',    label: 'Activity (mol/g/h) *', type: 'number', step: '0.01', required: true },
                { key: 'selectivity', label: 'Selectivity (0–1)',     type: 'number', step: '0.01', required: false },
                { key: 'stability',   label: 'Stability (hours)',      type: 'number', step: '1',    required: false },
                { key: 'temperature', label: 'Temperature (°C)',       type: 'number', step: '1',    required: false },
                { key: 'pressure',    label: 'Pressure (bar)',         type: 'number', step: '0.1',  required: false },
                { key: 'researcher',  label: 'Researcher',             type: 'text',   step: '',     required: false },
              ].map(({ key, label, type, step, required }) => (
                <div key={key}>
                  <label className="block text-sm font-semibold mb-1 text-gray-700 dark:text-gray-300">
                    {label}
                  </label>
                  <input
                    type={type}
                    step={step || undefined}
                    required={required}
                    className="w-full p-2.5 border border-gray-300 dark:border-gray-600 rounded-lg
                               bg-white dark:bg-gray-700 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                    value={(form as any)[key]}
                    onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                  />
                </div>
              ))}
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white
                         font-semibold text-sm disabled:opacity-50 transition-colors"
            >
              {submitting ? 'Logging…' : 'Log Experiment'}
            </button>
          </form>
        </div>

        {/* ── CSV upload + history ── */}
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6">
            <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">Bulk CSV Upload</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              CSV columns: <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">
                candidate_id, activity, selectivity, stability, temperature, pressure, researcher
              </code>
            </p>
            <form onSubmit={handleCsvUpload} className="space-y-3">
              <input
                type="file"
                accept=".csv"
                onChange={e => setCsvFile(e.target.files?.[0] || null)}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4
                           file:rounded-lg file:border-0 file:text-sm file:font-semibold
                           file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100
                           dark:file:bg-blue-900 dark:file:text-blue-300"
              />
              <button
                type="submit"
                disabled={submitting || !csvFile}
                className="w-full py-2.5 rounded-lg bg-green-600 hover:bg-green-700 text-white
                           font-semibold text-sm disabled:opacity-50 transition-colors"
              >
                {submitting ? 'Uploading…' : 'Upload CSV'}
              </button>
            </form>

            {/* Sample CSV download */}
            <button
              onClick={() => {
                const sample = 'candidate_id,activity,selectivity,stability,temperature,pressure,researcher\nzsm-5-ga-001,2.4,0.91,520,350,1,lab_user\n'
                const blob = new Blob([sample], { type: 'text/csv' })
                const a = document.createElement('a')
                a.href = URL.createObjectURL(blob)
                a.download = 'sample_experiments.csv'
                a.click()
              }}
              className="mt-3 text-xs text-blue-600 dark:text-blue-400 hover:underline"
            >
              Download sample CSV template
            </button>
          </div>

          {/* Session history */}
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6">
            <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">Session Log</h2>
            {history.length === 0 ? (
              <p className="text-sm text-gray-400">No experiments logged this session.</p>
            ) : (
              <div className="space-y-2">
                {history.map((h, i) => (
                  <div key={i} className="flex items-center justify-between text-sm
                                          border-b border-gray-100 dark:border-gray-700 pb-2">
                    <span className="font-mono text-gray-600 dark:text-gray-400 truncate max-w-[180px]">
                      {h.experiment_id}
                    </span>
                    <span className={`font-semibold ${discrepancyColor(h.discrepancy)}`}>
                      {(h.discrepancy * 100).toFixed(1)}% err
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function ExperimentsPage() {
  return (
    <Suspense fallback={<div className="p-12 text-center text-gray-400">Loading…</div>}>
      <ExperimentsContent />
    </Suspense>
  )
}
