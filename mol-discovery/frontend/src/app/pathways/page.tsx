'use client'

import React, { useState, useEffect } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface EnzymeResult {
  name:               string
  ec_number:          string
  organism:           string
  thermostability:    number
  activity:           number
  km_mm:              number
  kcat_per_s:         number
  suggested_mutations: string[]
  notes:              string
}

interface Modification {
  type:        string
  target_gene: string
  description: string
  confidence:  number
  rationale:   string
}

interface Bottleneck {
  enzyme:           string
  ec_number:        string
  current_activity: number
  kcat_per_s:       number
  priority:         string
  suggested_fix:    string
}

interface PathwayResult {
  pathway_type:              string
  target_reaction:           string
  recommended_microorganism: string
  organism_profile:          Record<string, any>
  enzymes:                   EnzymeResult[]
  genetic_modifications:     Modification[]
  predicted_yield:           number
  bottlenecks:               Bottleneck[]
  flux_distribution:         Record<string, number>
  confidence_score:          number
  pathway_steps:             number
}

interface PathwayType {
  id:    string
  label: string
}

interface Organism {
  id:      string
  name:    string
  profile: Record<string, any>
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function ModBadge({ type }: { type: string }) {
  const styles: Record<string, string> = {
    knockout:   'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
    overexpress:'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
    insert:     'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
    crispr:     'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
  }
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${styles[type] ?? 'bg-gray-100 text-gray-600'}`}>
      {type}
    </span>
  )
}

function ConfidenceBar({ value }: { value: number }) {
  const pct   = Math.round(value * 100)
  const color = pct >= 85 ? 'bg-green-500' : pct >= 70 ? 'bg-yellow-500' : 'bg-red-400'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
        <div className={`${color} h-1.5 rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono w-8 text-right text-gray-500">{pct}%</span>
    </div>
  )
}

function ActivityDot({ value }: { value: number }) {
  const color = value >= 0.85 ? 'bg-green-500' : value >= 0.70 ? 'bg-yellow-500' : 'bg-red-400'
  return <span className={`inline-block w-2 h-2 rounded-full ${color} mr-1`} />
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function PathwayDesignerPage() {
  const [reaction, setReaction]   = useState('')
  const [organism, setOrganism]   = useState('')
  const [loading, setLoading]     = useState(false)
  const [result, setResult]       = useState<PathwayResult | null>(null)
  const [error, setError]         = useState('')
  const [pathwayTypes, setPathwayTypes] = useState<PathwayType[]>([])
  const [organisms, setOrganisms] = useState<Organism[]>([])
  const [activeTab, setActiveTab] = useState<'enzymes' | 'modifications' | 'flux'>('enzymes')

  // Load reference data
  useEffect(() => {
    fetch(`${API}/api/biology/pathway/types`)
      .then(r => r.json())
      .then(d => setPathwayTypes(d.pathways || []))
      .catch(() => {})

    fetch(`${API}/api/biology/microorganisms`)
      .then(r => r.json())
      .then(d => setOrganisms(d.microorganisms || []))
      .catch(() => {})
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!reaction.trim()) return
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await fetch(`${API}/api/biology/pathway/design`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          target_reaction:     reaction,
          organism_preference: organism || null,
        }),
      })
      if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`)
      setResult(await res.json())
      setActiveTab('enzymes')
    } catch (err: any) {
      setError(err.message || 'Design failed')
    } finally {
      setLoading(false)
    }
  }

  const EXAMPLES = [
    'ethanol to jet fuel hydrocarbons',
    'cellulose degradation to glucose',
    'CO2 fixation to organic acids',
    'lignin valorization to vanillin',
    'fatty acid synthesis for biodiesel',
    'terpenoid biosynthesis farnesol',
  ]

  const TabBtn = ({ id, label }: { id: typeof activeTab; label: string }) => (
    <button
      onClick={() => setActiveTab(id)}
      className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${
        activeTab === id
          ? 'bg-green-600 text-white'
          : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
      }`}
    >
      {label}
    </button>
  )

  return (
    <div className="max-w-7xl mx-auto py-10 px-4 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Metabolic Pathway Designer
        </h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Design synthetic biology pathways for sustainable chemical production.
          Select enzymes, microorganisms, and genetic modifications.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* ── Input panel ── */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6">
            <h2 className="text-lg font-bold mb-4 text-gray-900 dark:text-white">
              Design Parameters
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold mb-1 text-gray-700 dark:text-gray-300">
                  Target Reaction
                </label>
                <textarea
                  rows={2}
                  value={reaction}
                  onChange={e => setReaction(e.target.value)}
                  placeholder="e.g. ethanol to jet fuel hydrocarbons"
                  className="w-full p-2.5 border border-gray-300 dark:border-gray-600 rounded-lg
                             bg-white dark:bg-gray-700 text-sm focus:ring-2 focus:ring-green-500
                             focus:outline-none resize-none"
                  required
                />
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {EXAMPLES.map(ex => (
                    <button
                      key={ex}
                      type="button"
                      onClick={() => setReaction(ex)}
                      className="text-xs px-2 py-0.5 rounded-full border border-green-300
                                 text-green-700 dark:border-green-700 dark:text-green-400
                                 hover:bg-green-50 dark:hover:bg-green-900/20"
                    >
                      {ex}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold mb-1 text-gray-700 dark:text-gray-300">
                  Host Organism (optional)
                </label>
                <select
                  value={organism}
                  onChange={e => setOrganism(e.target.value)}
                  className="w-full p-2.5 border border-gray-300 dark:border-gray-600 rounded-lg
                             bg-white dark:bg-gray-700 text-sm focus:ring-2 focus:ring-green-500
                             focus:outline-none"
                >
                  <option value="">Auto-select best organism</option>
                  {organisms.map(o => (
                    <option key={o.id} value={o.id}>{o.name}</option>
                  ))}
                </select>
              </div>

              <button
                type="submit"
                disabled={loading || !reaction.trim()}
                className="w-full py-2.5 rounded-lg bg-green-600 hover:bg-green-700 text-white
                           font-semibold text-sm disabled:opacity-50 transition-colors"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                    Designing pathway…
                  </span>
                ) : 'Design Pathway'}
              </button>
            </form>

            {error && (
              <div className="mt-3 bg-red-50 dark:bg-red-900/20 border border-red-300
                              dark:border-red-700 rounded-lg px-3 py-2 text-sm
                              text-red-700 dark:text-red-300">
                {error}
              </div>
            )}
          </div>

          {/* Pathway types reference */}
          {pathwayTypes.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-5">
              <h3 className="text-sm font-bold mb-3 text-gray-700 dark:text-gray-300 uppercase tracking-wide">
                Supported Pathways
              </h3>
              <ul className="space-y-1.5">
                {pathwayTypes.map(pt => (
                  <li key={pt.id}
                      onClick={() => setReaction(pt.label.split('(')[0].trim())}
                      className="text-sm text-gray-600 dark:text-gray-400 cursor-pointer
                                 hover:text-green-600 dark:hover:text-green-400 flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-500 flex-shrink-0" />
                    {pt.label}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* ── Results panel ── */}
        <div className="lg:col-span-3">
          {!result && !loading && (
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-12
                            flex flex-col items-center justify-center text-gray-400">
              <svg className="w-16 h-16 mb-4 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1}
                  d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" />
              </svg>
              <p className="text-sm">Enter a target reaction to design a pathway</p>
            </div>
          )}

          {result && (
            <div className="space-y-4">
              {/* Summary cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { label: 'Predicted Yield', value: `${(result.predicted_yield * 100).toFixed(1)}%`,
                    accent: 'text-green-600' },
                  { label: 'Confidence',      value: `${(result.confidence_score * 100).toFixed(0)}%`,
                    accent: 'text-blue-600' },
                  { label: 'Pathway Steps',   value: result.pathway_steps,
                    accent: 'text-gray-900 dark:text-white' },
                  { label: 'Bottlenecks',     value: result.bottlenecks.length,
                    accent: result.bottlenecks.length > 0 ? 'text-orange-600' : 'text-green-600' },
                ].map(({ label, value, accent }) => (
                  <div key={label} className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-4">
                    <div className="text-xs text-gray-500 dark:text-gray-400">{label}</div>
                    <div className={`text-2xl font-bold mt-0.5 ${accent}`}>{value}</div>
                  </div>
                ))}
              </div>

              {/* Organism */}
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-5">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mb-0.5">
                      Recommended Host Organism
                    </div>
                    <div className="font-bold text-gray-900 dark:text-white text-lg">
                      {result.recommended_microorganism}
                    </div>
                  </div>
                  <span className="text-xs px-2 py-1 bg-green-100 dark:bg-green-900/30
                                   text-green-700 dark:text-green-300 rounded-full font-semibold">
                    {result.pathway_type.replace(/_/g, ' ')}
                  </span>
                </div>
                {result.organism_profile?.strengths && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {(result.organism_profile.strengths as string[]).map(s => (
                      <span key={s} className="text-xs px-2 py-0.5 bg-blue-50 dark:bg-blue-900/20
                                               text-blue-700 dark:text-blue-300 rounded-full">
                        {s}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Tabs */}
              <div className="flex gap-2 bg-gray-100 dark:bg-gray-800 rounded-xl p-1 w-fit">
                <TabBtn id="enzymes"       label={`Enzymes (${result.enzymes.length})`} />
                <TabBtn id="modifications" label={`Modifications (${result.genetic_modifications.length})`} />
                <TabBtn id="flux"          label="Flux" />
              </div>

              {/* Enzymes tab */}
              {activeTab === 'enzymes' && (
                <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md overflow-hidden">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                        <th className="px-4 py-3 text-left font-semibold">Enzyme</th>
                        <th className="px-4 py-3 text-left font-semibold">EC</th>
                        <th className="px-4 py-3 text-left font-semibold">Activity</th>
                        <th className="px-4 py-3 text-left font-semibold">kcat (s⁻¹)</th>
                        <th className="px-4 py-3 text-left font-semibold">Mutations</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.enzymes.map((e, i) => (
                        <tr key={i}
                            className="border-t border-gray-100 dark:border-gray-700 hover:bg-gray-50
                                       dark:hover:bg-gray-700/50">
                          <td className="px-4 py-3">
                            <div className="font-medium text-gray-900 dark:text-white">
                              <ActivityDot value={e.activity} />{e.name}
                            </div>
                            <div className="text-xs text-gray-400 mt-0.5">{e.organism}</div>
                            {e.notes && (
                              <div className="text-xs text-blue-600 dark:text-blue-400 mt-0.5 italic">
                                {e.notes}
                              </div>
                            )}
                          </td>
                          <td className="px-4 py-3 font-mono text-xs text-gray-500">{e.ec_number}</td>
                          <td className="px-4 py-3 w-28">
                            <ConfidenceBar value={e.activity} />
                          </td>
                          <td className="px-4 py-3 font-mono text-xs">{e.kcat_per_s}</td>
                          <td className="px-4 py-3">
                            {e.suggested_mutations.length > 0 ? (
                              <div className="flex flex-wrap gap-1">
                                {e.suggested_mutations.map(m => (
                                  <span key={m}
                                        className="text-xs px-1.5 py-0.5 bg-purple-100 dark:bg-purple-900/30
                                                   text-purple-700 dark:text-purple-300 rounded font-mono">
                                    {m}
                                  </span>
                                ))}
                              </div>
                            ) : (
                              <span className="text-xs text-gray-400">—</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>

                  {/* Bottlenecks */}
                  {result.bottlenecks.length > 0 && (
                    <div className="border-t border-gray-100 dark:border-gray-700 p-4">
                      <div className="text-sm font-semibold text-orange-600 dark:text-orange-400 mb-2">
                        Rate-Limiting Steps
                      </div>
                      <div className="space-y-2">
                        {result.bottlenecks.map((b, i) => (
                          <div key={i} className="flex items-start gap-2 text-sm">
                            <span className={`flex-shrink-0 px-1.5 py-0.5 rounded text-xs font-semibold ${
                              b.priority === 'high'
                                ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
                                : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300'
                            }`}>
                              {b.priority}
                            </span>
                            <div>
                              <span className="font-medium text-gray-900 dark:text-white">{b.enzyme}</span>
                              <span className="text-gray-400 mx-1">—</span>
                              <span className="text-gray-600 dark:text-gray-400">{b.suggested_fix}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Modifications tab */}
              {activeTab === 'modifications' && (
                <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-5 space-y-3">
                  {result.genetic_modifications.length === 0 ? (
                    <p className="text-gray-400 text-sm">No modifications recommended.</p>
                  ) : (
                    result.genetic_modifications.map((mod, i) => (
                      <div key={i}
                           className="border border-gray-100 dark:border-gray-700 rounded-xl p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <ModBadge type={mod.type} />
                          <span className="font-mono font-bold text-gray-900 dark:text-white">
                            {mod.target_gene}
                          </span>
                          <span className="ml-auto text-xs text-gray-400">
                            {(mod.confidence * 100).toFixed(0)}% confidence
                          </span>
                        </div>
                        <p className="text-sm text-gray-700 dark:text-gray-300">{mod.description}</p>
                        {mod.rationale && (
                          <p className="text-xs text-blue-600 dark:text-blue-400 mt-1 italic">
                            {mod.rationale}
                          </p>
                        )}
                        <div className="mt-2">
                          <ConfidenceBar value={mod.confidence} />
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Flux tab */}
              {activeTab === 'flux' && (
                <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-5">
                  <h3 className="font-bold mb-4 text-gray-900 dark:text-white">
                    Flux Distribution
                  </h3>
                  <div className="space-y-2">
                    {Object.entries(result.flux_distribution).map(([step, flux]) => (
                      <div key={step}>
                        <div className="flex justify-between text-xs mb-0.5">
                          <span className="text-gray-600 dark:text-gray-400 font-mono">
                            {step.replace(/_/g, ' ')}
                          </span>
                          <span className="font-semibold text-gray-900 dark:text-white">
                            {flux.toFixed(3)}
                          </span>
                        </div>
                        <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-green-500 h-2 rounded-full"
                            style={{ width: `${Math.min(100, flux * 100)}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
