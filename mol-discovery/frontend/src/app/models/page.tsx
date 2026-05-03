'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { api, type ModelHealth } from '@/services/api'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface DriftFeature {
  psi:          number
  ks_statistic: number
  ks_p_value:   number
  jsd:          number
  drift:        boolean
  severity:     string
  ref_mean:     number
  new_mean:     number
}

interface DriftReport {
  drift_detected:   boolean
  severity:         string
  max_psi:          number
  features:         Record<string, DriftFeature>
  drifted_features: string[]
  summary:          string
  suggestions:      string[]
  n_reference:      number
  n_new:            number
}

interface ModelVersion {
  version:       string
  samples_used:  number
  val_mae:       number | null
  val_r2:        number | null
  is_production: boolean
  promoted_at:   string | null
  created_at:    string | null
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function MetricBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-600 dark:text-gray-400">{label}</span>
        <span className="font-semibold text-gray-900 dark:text-white">{value.toFixed(1)}%</span>
      </div>
      <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
        <div className={`${color} h-2.5 rounded-full transition-all duration-700`}
             style={{ width: `${Math.min(100, value)}%` }} />
      </div>
    </div>
  )
}

function StatCard({ label, value, sub, accent }: {
  label: string; value: string | number; sub?: string; accent?: string
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-5">
      <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">{label}</div>
      <div className={`text-3xl font-bold ${accent ?? 'text-gray-900 dark:text-white'}`}>{value}</div>
      {sub && <div className="text-xs text-gray-400 mt-1">{sub}</div>}
    </div>
  )
}

function PsiBar({ psi, label }: { psi: number; label: string }) {
  const pct   = Math.min(100, psi * 200)   // PSI 0.5 = 100%
  const color = psi < 0.10 ? 'bg-green-500' : psi < 0.20 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-gray-600 dark:text-gray-400 capitalize">{label}</span>
        <span className={`font-semibold ${psi >= 0.10 ? 'text-orange-600' : 'text-gray-500'}`}>
          PSI {psi.toFixed(3)}
        </span>
      </div>
      <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-2">
        <div className={`${color} h-2 rounded-full`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function ModelsPage() {
  const [health, setHealth]         = useState<ModelHealth | null>(null)
  const [loading, setLoading]       = useState(true)
  const [retraining, setRetraining] = useState(false)
  const [retrained, setRetrained]   = useState<string | null>(null)
  const [error, setError]           = useState('')

  const [drift, setDrift]           = useState<DriftReport | null>(null)
  const [driftLoading, setDriftLoading] = useState(false)

  const [versions, setVersions]     = useState<ModelVersion[]>([])
  const [versionsLoading, setVersionsLoading] = useState(false)

  const [tab, setTab] = useState<'health' | 'drift' | 'versions'>('health')

  // ── Fetch health ──────────────────────────────────────────────────────
  const fetchHealth = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      setHealth(await api.getModelHealth())
    } catch (e: any) {
      setError(e.message || 'Failed to fetch model health')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchHealth() }, [fetchHealth])

  // Poll while retraining is in progress
  useEffect(() => {
    if (!health?.retraining_in_progress) return
    const id = setInterval(fetchHealth, 3000)
    return () => clearInterval(id)
  }, [health?.retraining_in_progress, fetchHealth])

  // ── Retrain ───────────────────────────────────────────────────────────
  const handleRetrain = async (async_mode = false) => {
    setRetraining(true)
    setError('')
    setRetrained(null)
    try {
      const url = async_mode
        ? `${API}/api/model/retrain/async`
        : `${API}/api/model/retrain`
      const res = await fetch(url, { method: 'POST' })
      const data = await res.json()

      if (data.status === 'success') {
        setRetrained(`Model updated to ${data.new_model_version} — val MAE: ${data.val_mae ?? 'n/a'}, R²: ${data.val_r2 ?? 'n/a'}`)
      } else if (data.status === 'queued') {
        setRetrained('Retraining started in background. This page will refresh automatically.')
      } else if (data.status === 'rolled_back') {
        setRetrained('Retraining complete but new model did not improve — keeping current version.')
      } else {
        setRetrained(`Status: ${data.status}${data.reason ? ` — ${data.reason}` : ''}`)
      }
      await fetchHealth()
    } catch (e: any) {
      setError(e.message || 'Retraining failed')
    } finally {
      setRetraining(false)
    }
  }

  // ── Drift ─────────────────────────────────────────────────────────────
  const fetchDrift = async () => {
    setDriftLoading(true)
    try {
      const res = await fetch(`${API}/api/model/drift?window_days=30`)
      setDrift(await res.json())
    } catch (e: any) {
      setError(e.message)
    } finally {
      setDriftLoading(false)
    }
  }

  useEffect(() => {
    if (tab === 'drift' && !drift) fetchDrift()
  }, [tab])

  // ── Versions ──────────────────────────────────────────────────────────
  const fetchVersions = async () => {
    setVersionsLoading(true)
    try {
      const res = await fetch(`${API}/api/model/versions`)
      const data = await res.json()
      setVersions(data.versions || [])
    } catch (e: any) {
      setError(e.message)
    } finally {
      setVersionsLoading(false)
    }
  }

  useEffect(() => {
    if (tab === 'versions' && versions.length === 0) fetchVersions()
  }, [tab])

  // ── Render ────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400">
        <svg className="animate-spin h-6 w-6 mr-2" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
        Loading model health…
      </div>
    )
  }

  const accuracy      = health?.overall_accuracy ?? 0
  const accuracyColor = accuracy >= 85 ? 'text-green-600' : accuracy >= 70 ? 'text-yellow-600' : 'text-red-600'

  const TabBtn = ({ id, label }: { id: typeof tab; label: string }) => (
    <button
      onClick={() => setTab(id)}
      className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${
        tab === id
          ? 'bg-blue-600 text-white'
          : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
      }`}
    >
      {label}
    </button>
  )

  return (
    <div className="max-w-5xl mx-auto py-10 px-4 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Model Health</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Monitor accuracy, detect data drift, and manage active learning.
          </p>
        </div>
        <button onClick={fetchHealth}
          className="text-sm px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600
                     hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
          Refresh
        </button>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/30 border border-red-300 dark:border-red-700
                        rounded-lg px-4 py-3 text-sm text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {/* Retraining in progress banner */}
      {health?.retraining_in_progress && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-300 dark:border-blue-700
                        rounded-xl px-4 py-3 flex items-center gap-3 text-sm
                        text-blue-800 dark:text-blue-200">
          <svg className="animate-spin h-4 w-4 flex-shrink-0" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          <span>Retraining in progress — page refreshes automatically every 3 s.</span>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 bg-gray-100 dark:bg-gray-800 rounded-xl p-1 w-fit">
        <TabBtn id="health"   label="Health" />
        <TabBtn id="drift"    label="Drift Report" />
        <TabBtn id="versions" label="Version History" />
      </div>

      {/* ── Tab: Health ── */}
      {tab === 'health' && (
        <div className="space-y-6">
          {/* KPI cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Overall Accuracy" value={`${accuracy.toFixed(1)}%`} accent={accuracyColor} />
            <StatCard label="Experiments" value={health?.experiment_count ?? 0} sub="total logged" />
            <StatCard
              label="Discrepancies"
              value={health?.total_discrepancies ?? 0}
              sub={`avg ${health?.average_error?.toFixed(1) ?? 0}% error`}
              accent={(health?.total_discrepancies ?? 0) > 5 ? 'text-yellow-600' : undefined}
            />
            <StatCard
              label="Pending"
              value={health?.pending_experiments ?? 0}
              sub={health?.retraining_ready ? 'Retraining recommended' : 'No action needed'}
              accent={health?.retraining_ready ? 'text-orange-600' : undefined}
            />
          </div>

          {/* Model version + validation metrics */}
          {(health?.model_version || health?.val_mae != null) && (
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-5">
              <h2 className="text-lg font-bold mb-3 text-gray-900 dark:text-white">
                Current Model
              </h2>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <div className="text-gray-500 dark:text-gray-400">Version</div>
                  <div className="font-mono font-semibold text-gray-900 dark:text-white mt-0.5">
                    {health?.model_version ?? 'demo_v1'}
                  </div>
                </div>
                {health?.val_mae != null && (
                  <div>
                    <div className="text-gray-500 dark:text-gray-400">Val MAE</div>
                    <div className="font-semibold text-gray-900 dark:text-white mt-0.5">
                      {health.val_mae.toFixed(4)}
                    </div>
                  </div>
                )}
                {health?.val_r2 != null && (
                  <div>
                    <div className="text-gray-500 dark:text-gray-400">Val R²</div>
                    <div className="font-semibold text-gray-900 dark:text-white mt-0.5">
                      {health.val_r2.toFixed(4)}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Accuracy bars */}
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6 space-y-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">Prediction Accuracy</h2>
            <MetricBar label="Overall accuracy" value={accuracy} color="bg-blue-500" />
            {health?.max_error != null && (
              <MetricBar
                label={`Max single error (${health.max_error.toFixed(1)}%)`}
                value={Math.min(100, health.max_error)}
                color="bg-red-400"
              />
            )}
          </div>

          {/* Per-family */}
          {health?.family_performance && Object.keys(health.family_performance).length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6">
              <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                Performance by Catalyst Family
              </h2>
              <div className="space-y-3">
                {Object.entries(health.family_performance).map(([family, data]) => {
                  const acc = typeof data === 'object' ? (data as any).accuracy : data
                  return (
                    <MetricBar
                      key={family}
                      label={`${family} (${typeof data === 'object' ? (data as any).samples : '?'} samples)`}
                      value={acc}
                      color="bg-purple-500"
                    />
                  )
                })}
              </div>
            </div>
          )}

          {/* Retraining panel */}
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6 space-y-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">Active Learning</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Fine-tunes the GNN on your latest experimental data with validation gating —
              new weights are only promoted if validation MAE improves.
            </p>

            {health?.retraining_ready && (
              <div className="bg-orange-50 dark:bg-orange-900/20 border border-orange-300
                              dark:border-orange-700 rounded-lg px-4 py-3 text-sm
                              text-orange-800 dark:text-orange-200 font-medium">
                {health.pending_experiments} unanalyzed experiments — retraining recommended.
              </div>
            )}

            {retrained && (
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-300
                              dark:border-green-700 rounded-lg px-4 py-3 text-sm
                              text-green-800 dark:text-green-200">
                {retrained}
              </div>
            )}

            <div className="flex gap-3 flex-wrap">
              <button
                onClick={() => handleRetrain(false)}
                disabled={retraining || !!health?.retraining_in_progress}
                className="px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white
                           font-semibold text-sm disabled:opacity-50 transition-colors"
              >
                {retraining ? (
                  <span className="flex items-center gap-2">
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                    Retraining…
                  </span>
                ) : 'Retrain Now'}
              </button>
              <button
                onClick={() => handleRetrain(true)}
                disabled={retraining || !!health?.retraining_in_progress}
                className="px-5 py-2.5 rounded-lg border border-blue-600 text-blue-600
                           dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20
                           font-semibold text-sm disabled:opacity-50 transition-colors"
              >
                Retrain in Background
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Tab: Drift ── */}
      {tab === 'drift' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">Data Drift Report</h2>
            <button onClick={fetchDrift} disabled={driftLoading}
              className="text-sm px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600
                         hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 transition-colors">
              {driftLoading ? 'Checking…' : 'Refresh'}
            </button>
          </div>

          {driftLoading && !drift && (
            <div className="flex items-center justify-center h-32 text-gray-400 gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Analysing distributions…
            </div>
          )}

          {drift && (
            <>
              {/* Summary banner */}
              <div className={`rounded-xl px-4 py-3 text-sm font-medium border ${
                drift.drift_detected
                  ? drift.severity === 'high'
                    ? 'bg-red-50 dark:bg-red-900/20 border-red-300 dark:border-red-700 text-red-800 dark:text-red-200'
                    : 'bg-orange-50 dark:bg-orange-900/20 border-orange-300 dark:border-orange-700 text-orange-800 dark:text-orange-200'
                  : 'bg-green-50 dark:bg-green-900/20 border-green-300 dark:border-green-700 text-green-800 dark:text-green-200'
              }`}>
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-bold capitalize">{drift.severity} drift</span>
                  <span className="text-xs opacity-70">
                    ({drift.n_reference} reference / {drift.n_new} new experiments)
                  </span>
                </div>
                {drift.summary}
              </div>

              {/* Per-feature PSI bars */}
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6 space-y-3">
                <h3 className="font-bold text-gray-900 dark:text-white">Feature Drift (PSI)</h3>
                <div className="text-xs text-gray-400 mb-2">
                  PSI &lt; 0.10 = stable · 0.10–0.20 = moderate · &gt; 0.20 = significant
                </div>
                {Object.entries(drift.features).map(([feat, rep]) => (
                  <div key={feat}>
                    <PsiBar psi={rep.psi} label={feat} />
                    <div className="flex gap-4 text-xs text-gray-400 mt-0.5 ml-1">
                      <span>ref mean: {rep.ref_mean}</span>
                      <span>new mean: {rep.new_mean}</span>
                      <span>KS p={rep.ks_p_value}</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Suggestions */}
              {drift.suggestions.length > 0 && (
                <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6">
                  <h3 className="font-bold mb-3 text-gray-900 dark:text-white">Recommendations</h3>
                  <ul className="space-y-2">
                    {drift.suggestions.map((s, i) => (
                      <li key={i} className="flex gap-2 text-sm text-gray-600 dark:text-gray-400">
                        <span className="text-blue-500 flex-shrink-0">•</span>
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* ── Tab: Versions ── */}
      {tab === 'versions' && (
        <div className="space-y-4">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">Model Version History</h2>

          {versionsLoading && (
            <div className="flex items-center justify-center h-32 text-gray-400 gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Loading…
            </div>
          )}

          {!versionsLoading && versions.length === 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-8 text-center text-gray-400">
              No model versions recorded yet. Trigger retraining to create the first entry.
            </div>
          )}

          {versions.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                    <th className="px-4 py-3 text-left font-semibold">Version</th>
                    <th className="px-4 py-3 text-left font-semibold">Samples</th>
                    <th className="px-4 py-3 text-left font-semibold">Val MAE</th>
                    <th className="px-4 py-3 text-left font-semibold">Val R²</th>
                    <th className="px-4 py-3 text-left font-semibold">Status</th>
                    <th className="px-4 py-3 text-left font-semibold">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {versions.map(v => (
                    <tr key={v.version}
                        className="border-t border-gray-100 dark:border-gray-700">
                      <td className="px-4 py-3 font-mono text-gray-900 dark:text-white">
                        {v.version}
                      </td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                        {v.samples_used}
                      </td>
                      <td className="px-4 py-3 font-mono">
                        {v.val_mae != null ? v.val_mae.toFixed(4) : '—'}
                      </td>
                      <td className="px-4 py-3 font-mono">
                        {v.val_r2 != null ? v.val_r2.toFixed(4) : '—'}
                      </td>
                      <td className="px-4 py-3">
                        {v.is_production ? (
                          <span className="px-2 py-0.5 bg-green-100 dark:bg-green-900/30
                                           text-green-700 dark:text-green-300 rounded-full text-xs font-semibold">
                            production
                          </span>
                        ) : (
                          <span className="text-gray-400 text-xs">archived</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-gray-400 text-xs">
                        {v.created_at ? new Date(v.created_at).toLocaleDateString() : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
