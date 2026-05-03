'use client'

import React, { useState, useCallback, useEffect } from 'react'
import Link from 'next/link'
import { api, type Candidate, type DiscoveryResponse } from '@/services/api'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ── Quick-pick reactions ──────────────────────────────────────────────────
const EXAMPLE_REACTIONS = [
  'ethanol to jet fuel',
  'CO2 + H2 → methanol',
  'N2 + H2 → ammonia',
  'methane oxidation to methanol',
]

// ── Helpers ───────────────────────────────────────────────────────────────
function Badge({ type }: { type: string }) {
  const cls =
    type === 'novel'
      ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
      : 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${cls}`}>
      {type}
    </span>
  )
}

function ScoreBar({ value }: { value: number }) {
  const pct = Math.min(100, Math.round(value * 100))
  const color =
    pct >= 70 ? 'bg-green-500' : pct >= 45 ? 'bg-yellow-500' : 'bg-red-400'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
        <div className={`${color} h-2 rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono w-10 text-right">{value.toFixed(3)}</span>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────
export default function DiscoveryPage() {
  const [reaction, setReaction] = useState('')
  const [minStability, setMinStability] = useState(200)
  const [maxTemp, setMaxTemp] = useState(500)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<DiscoveryResponse | null>(null)
  const [selected, setSelected] = useState<Candidate | null>(null)
  const [sortKey, setSortKey] = useState<keyof Candidate>('score')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [backendOk, setBackendOk] = useState<boolean | null>(null)

  // Check backend connectivity on mount
  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then(() => setBackendOk(true))
      .catch(() => setBackendOk(false))
  }, [])

  const handleSort = (key: keyof Candidate) => {
    if (sortKey === key) setSortDir(d => (d === 'asc' ? 'desc' : 'asc'))
    else { setSortKey(key); setSortDir('desc') }
  }

  const sortedCandidates = result
    ? [...result.candidates].sort((a, b) => {
        const av = a[sortKey] as number
        const bv = b[sortKey] as number
        return sortDir === 'asc' ? av - bv : bv - av
      })
    : []

  const handleSubmit = useCallback(async () => {
    if (!reaction.trim()) return
    setLoading(true)
    setError('')
    setResult(null)
    setSelected(null)
    try {
      const res = await api.startDiscovery(reaction, {
        min_stability: minStability,
        max_temperature: maxTemp,
      })
      setResult(res)
    } catch (e: any) {
      setError(e.message || 'Discovery failed')
    } finally {
      setLoading(false)
    }
  }, [reaction, minStability, maxTemp])

  const handleExport = () => {
    if (!result) return
    const header = 'name,type,activity,selectivity,stability,uncertainty,score\n'
    const rows = result.candidates
      .map(c =>
        [
          `"${c.name}"`,
          c.type,
          c.predicted_activity,
          c.predicted_selectivity,
          c.predicted_stability,
          c.uncertainty,
          c.score,
        ].join(',')
      )
      .join('\n')
    const blob = new Blob([header + rows], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `discovery_${result.run_id.slice(0, 8)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const SortIcon = ({ col }: { col: keyof Candidate }) =>
    sortKey === col ? (
      <span className="ml-1">{sortDir === 'desc' ? '↓' : '↑'}</span>
    ) : (
      <span className="ml-1 opacity-30">↕</span>
    )

  return (
    <div className="max-w-7xl mx-auto py-10 px-4 space-y-8">
      {/* ── Header ── */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Catalyst Discovery
        </h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Enter a target reaction and let the AI screen thousands of candidates.
        </p>
      </div>

      {/* ── Backend status banner ── */}
      {backendOk === false && (
        <div className="bg-amber-50 dark:bg-amber-900/30 border border-amber-300 dark:border-amber-700
                        rounded-xl px-4 py-3 text-sm text-amber-800 dark:text-amber-200">
          <strong>Backend offline.</strong> Start the backend first:
          <code className="ml-2 bg-amber-100 dark:bg-amber-900 px-2 py-0.5 rounded font-mono text-xs">
            uvicorn app.main:app --reload --port 8000
          </code>
          <span className="ml-2 text-amber-600 dark:text-amber-400">
            (from mol-discovery/backend with venv active)
          </span>
        </div>
      )}

      {/* ── Input panel ── */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6 space-y-5">
        <div>
          <label className="block text-sm font-semibold mb-1 text-gray-700 dark:text-gray-300">
            Target Reaction
          </label>
          <textarea
            rows={2}
            className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                       focus:ring-2 focus:ring-blue-500 focus:outline-none resize-none"
            placeholder="e.g. ethanol to jet fuel  |  CO2 + H2 → methanol"
            value={reaction}
            onChange={e => setReaction(e.target.value)}
          />
          <div className="flex flex-wrap gap-2 mt-2">
            {EXAMPLE_REACTIONS.map(r => (
              <button
                key={r}
                onClick={() => setReaction(r)}
                className="text-xs px-3 py-1 rounded-full border border-blue-300 text-blue-600
                           dark:border-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900"
              >
                {r}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-semibold mb-1 text-gray-700 dark:text-gray-300">
              Min Stability: {minStability} h
            </label>
            <input
              type="range" min={50} max={600} step={10}
              value={minStability}
              onChange={e => setMinStability(Number(e.target.value))}
              className="w-full accent-blue-600"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold mb-1 text-gray-700 dark:text-gray-300">
              Max Temperature: {maxTemp} °C
            </label>
            <input
              type="range" min={100} max={800} step={25}
              value={maxTemp}
              onChange={e => setMaxTemp(Number(e.target.value))}
              className="w-full accent-blue-600"
            />
          </div>
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading || !reaction.trim()}
          className="w-full sm:w-auto px-8 py-3 rounded-lg font-semibold text-white
                     bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed
                     transition-colors"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Running discovery…
            </span>
          ) : (
            'Start Discovery'
          )}
        </button>

        {error && (
          <div className="bg-red-50 dark:bg-red-900/30 border border-red-300 dark:border-red-700
                          text-red-700 dark:text-red-300 rounded-lg px-4 py-3 text-sm space-y-1">
            <div className="font-semibold">Discovery failed</div>
            <div>{error}</div>
            {error.includes('fetch') || error.includes('network') || error.includes('Failed to fetch') ? (
              <div className="text-xs mt-1 text-red-500 dark:text-red-400">
                Cannot reach backend at <code className="font-mono">{API_BASE}</code>.
                Make sure uvicorn is running on port 8000.
              </div>
            ) : error.includes('422') ? (
              <div className="text-xs mt-1 text-red-500 dark:text-red-400">
                Validation error — try a reaction like &quot;ethanol to jet fuel&quot; or &quot;CO2 + H2 → methanol&quot;.
              </div>
            ) : null}
          </div>
        )}
      </div>

      {/* ── Results ── */}
      {result && (
        <div className="space-y-4">
          {/* Stats bar */}
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex gap-4 text-sm text-gray-600 dark:text-gray-400">
              <span>
                <strong className="text-gray-900 dark:text-white">{result.total_candidates}</strong> candidates
              </span>
              <span>
                <strong className="text-blue-600">{result.known_count}</strong> known
              </span>
              <span>
                <strong className="text-purple-600">{result.novel_count}</strong> AI-generated
              </span>
              <span className="text-xs font-mono text-gray-400">run: {result.run_id.slice(0, 8)}</span>
            </div>
            <button
              onClick={handleExport}
              className="text-sm px-4 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600
                         hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              Export CSV
            </button>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            {/* Table */}
            <div className="xl:col-span-2 bg-white dark:bg-gray-800 rounded-2xl shadow-md overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                      <th className="px-4 py-3 text-left font-semibold">#</th>
                      <th className="px-4 py-3 text-left font-semibold">Catalyst</th>
                      <th
                        className="px-4 py-3 text-left font-semibold cursor-pointer hover:text-blue-600"
                        onClick={() => handleSort('score')}
                      >
                        Score <SortIcon col="score" />
                      </th>
                      <th
                        className="px-4 py-3 text-left font-semibold cursor-pointer hover:text-blue-600"
                        onClick={() => handleSort('predicted_activity')}
                      >
                        Activity <SortIcon col="predicted_activity" />
                      </th>
                      <th
                        className="px-4 py-3 text-left font-semibold cursor-pointer hover:text-blue-600"
                        onClick={() => handleSort('predicted_selectivity')}
                      >
                        Sel. <SortIcon col="predicted_selectivity" />
                      </th>
                      <th
                        className="px-4 py-3 text-left font-semibold cursor-pointer hover:text-blue-600"
                        onClick={() => handleSort('predicted_stability')}
                      >
                        Stab. <SortIcon col="predicted_stability" />
                      </th>
                      <th className="px-4 py-3 text-left font-semibold">Uncert.</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedCandidates.map((c, i) => (
                      <tr
                        key={c.id}
                        onClick={() => setSelected(c)}
                        className={`border-t border-gray-100 dark:border-gray-700 cursor-pointer
                                    transition-colors hover:bg-blue-50 dark:hover:bg-blue-900/20
                                    ${selected?.id === c.id ? 'bg-blue-50 dark:bg-blue-900/30' : ''}`}
                      >
                        <td className="px-4 py-3 text-gray-400 font-mono">{i + 1}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <Badge type={c.type} />
                            <span className="font-medium text-gray-900 dark:text-white truncate max-w-[200px]">
                              {c.name}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3 w-32">
                          <ScoreBar value={c.score} />
                        </td>
                        <td className="px-4 py-3 font-mono">{c.predicted_activity.toFixed(2)}</td>
                        <td className="px-4 py-3 font-mono">{(c.predicted_selectivity * 100).toFixed(1)}%</td>
                        <td className="px-4 py-3 font-mono">{c.predicted_stability}h</td>
                        <td className="px-4 py-3 font-mono text-gray-400">
                          ±{(c.uncertainty * 100).toFixed(0)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Detail panel */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6">
              {selected ? (
                <div className="space-y-4">
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-bold text-lg text-gray-900 dark:text-white leading-tight">
                      {selected.name}
                    </h3>
                    <Badge type={selected.type} />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { label: 'Score', value: selected.score.toFixed(3) },
                      { label: 'Activity', value: `${selected.predicted_activity.toFixed(2)} mol/g/h` },
                      { label: 'Selectivity', value: `${(selected.predicted_selectivity * 100).toFixed(1)}%` },
                      { label: 'Stability', value: `${selected.predicted_stability} h` },
                      { label: 'Uncertainty', value: `±${(selected.uncertainty * 100).toFixed(0)}%` },
                      ...(selected.novelty_score != null
                        ? [{ label: 'Novelty', value: selected.novelty_score.toFixed(2) }]
                        : []),
                    ].map(({ label, value }) => (
                      <div key={label} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                        <div className="text-xs text-gray-500 dark:text-gray-400">{label}</div>
                        <div className="font-semibold text-gray-900 dark:text-white mt-0.5">{value}</div>
                      </div>
                    ))}
                  </div>

                  {selected.details && (
                    <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-sm
                                    text-blue-800 dark:text-blue-200">
                      <div className="font-semibold mb-1">Rationale</div>
                      {selected.details}
                    </div>
                  )}

                  <Link
                    href={`/experiments?candidate_id=${selected.id}&name=${encodeURIComponent(selected.name)}`}
                    className="block w-full text-center py-2 rounded-lg bg-blue-600 hover:bg-blue-700
                               text-white font-semibold text-sm transition-colors"
                  >
                    Log Experiment for This Candidate
                  </Link>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-gray-400 py-12">
                  <svg className="w-12 h-12 mb-3 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                      d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5" />
                  </svg>
                  <p className="text-sm">Click a row to see details</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
