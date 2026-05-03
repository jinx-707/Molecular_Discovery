'use client'

/**
 * Enzyme Engineering page
 * -----------------------
 * Tabs:
 *   1. Mutation Predictor  — LLR scoring + heatmap
 *   2. Pathway Designer    — FBA flux map + knockout targets
 *   3. Gene Editing        — CRISPR gRNA design
 */

import React, { useState } from 'react'
import MutationHeatmap, { type LLRResult } from '@/components/MutationHeatmap'
import PathwayMapViewer, { type FluxData } from '@/components/PathwayMapViewer'
import GeneEditingViewer, { type GuideRNA } from '@/components/GeneEditingViewer'
import ProteinViewer3D from '@/components/ProteinViewer3D'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ── Demo sequence (TEM-1 β-lactamase fragment) ────────────────────────────
const DEMO_SEQUENCE =
  'MSIQHFRVALIPFFAAFCLPVFAHPETLVKVKDAEDQLGARVGYIELDLNSGKILESFRPEERFPMMSTFKVLLCGAVLSRVDAGQEQLGRRIHYSQNDLVEYSPVTEKHLTDGMTVRELCSAAITMSDNTAANLLLTTIGGPKELTAFLHNMGDHVTRLDRWEPELNEAIPNDERDTTMPVAMATTLRKLLTGELLTLASRQQLIDWMEADKVAGPLLRSALPAGWFIADKSGAGERGSRGIIAALGPDGKPSRIVVIYTTGSQATMDERNRQIAEIGASLIKHW'

type Tab = 'mutations' | 'pathway' | 'editing'

export default function EnzymePage() {
  const [tab, setTab] = useState<Tab>('mutations')

  // ── Mutation predictor state ──────────────────────────────────────────
  const [sequence, setSequence]     = useState(DEMO_SEQUENCE)
  const [topK, setTopK]             = useState(12)
  const [llrResults, setLlrResults] = useState<LLRResult[]>([])
  const [mutLoading, setMutLoading] = useState(false)
  const [mutError, setMutError]     = useState('')

  // ── Pathway designer state ────────────────────────────────────────────
  const [targetRxn, setTargetRxn]   = useState('EX_etoh_e')
  const [koGenes, setKoGenes]       = useState('')
  const [fluxData, setFluxData]     = useState<FluxData | null>(null)
  const [fluxLoading, setFluxLoading] = useState(false)
  const [fluxError, setFluxError]   = useState('')

  // ── Gene editing state ────────────────────────────────────────────────
  const [targetGene, setTargetGene] = useState('adhE')
  const [nGuides, setNGuides]       = useState(5)
  const [guides, setGuides]         = useState<GuideRNA[]>([])
  const [grnaLoading, setGrnaLoading] = useState(false)
  const [grnaError, setGrnaError]   = useState('')

  // ── Handlers ─────────────────────────────────────────────────────────

  const handleSuggestMutations = async () => {
    setMutLoading(true)
    setMutError('')
    try {
      const res = await fetch(`${API}/api/enzyme/suggest`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ sequence, top_k: topK, min_llr: 0.3 }),
      })
      if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`)
      const data = await res.json()
      setLlrResults(data.suggestions)
    } catch (e: any) {
      setMutError(e.message)
    } finally {
      setMutLoading(false)
    }
  }

  const handleRunFBA = async () => {
    setFluxLoading(true)
    setFluxError('')
    try {
      const knockouts = koGenes.split(',').map(s => s.trim()).filter(Boolean)
      const res = await fetch(`${API}/api/enzyme/flux`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          target_reaction: targetRxn || null,
          gene_knockouts:  knockouts.length ? knockouts : null,
        }),
      })
      if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`)
      setFluxData(await res.json())
    } catch (e: any) {
      setFluxError(e.message)
    } finally {
      setFluxLoading(false)
    }
  }

  const handleDesignGrna = async () => {
    setGrnaLoading(true)
    setGrnaError('')
    try {
      const res = await fetch(`${API}/api/enzyme/grna`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ target_gene: targetGene, n_guides: nGuides }),
      })
      if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`)
      const data = await res.json()
      setGuides(data.guides)
    } catch (e: any) {
      setGrnaError(e.message)
    } finally {
      setGrnaLoading(false)
    }
  }

  // ── Shared UI helpers ─────────────────────────────────────────────────

  const TabBtn = ({ id, label }: { id: Tab; label: string }) => (
    <button
      onClick={() => setTab(id)}
      className={`px-5 py-2.5 rounded-lg font-semibold text-sm transition-colors ${
        tab === id
          ? 'bg-blue-600 text-white shadow'
          : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
      }`}
    >
      {label}
    </button>
  )

  const RunBtn = ({
    onClick, loading, label,
  }: { onClick: () => void; loading: boolean; label: string }) => (
    <button
      onClick={onClick}
      disabled={loading}
      className="px-6 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white
                 font-semibold text-sm disabled:opacity-50 transition-colors"
    >
      {loading ? (
        <span className="flex items-center gap-2">
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          Running…
        </span>
      ) : label}
    </button>
  )

  const ErrorBox = ({ msg }: { msg: string }) =>
    msg ? (
      <div className="bg-red-50 dark:bg-red-900/30 border border-red-300 dark:border-red-700
                      rounded-lg px-4 py-3 text-sm text-red-700 dark:text-red-300">
        {msg}
      </div>
    ) : null

  // ── Render ────────────────────────────────────────────────────────────

  return (
    <div className="max-w-6xl mx-auto py-10 px-4 space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Enzyme Engineering
        </h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          AI-assisted mutation prediction, metabolic pathway design, and CRISPR guide RNA generation.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 bg-gray-100 dark:bg-gray-800 rounded-xl p-1 w-fit">
        <TabBtn id="mutations" label="Mutation Predictor" />
        <TabBtn id="pathway"   label="Pathway Designer" />
        <TabBtn id="editing"   label="Gene Editing" />
      </div>

      {/* ── Tab 1: Mutation Predictor ── */}
      {tab === 'mutations' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6 space-y-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              LLR Mutation Scoring
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Uses ESM-2 masked marginals to score every possible single-point mutation.
              Positive LLR = model considers the mutant more likely than wild-type.
            </p>

            <div>
              <label className="block text-sm font-semibold mb-1 text-gray-700 dark:text-gray-300">
                Protein Sequence (single-letter AA codes)
              </label>
              <textarea
                rows={4}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg
                           bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono text-xs
                           focus:ring-2 focus:ring-blue-500 focus:outline-none resize-none"
                value={sequence}
                onChange={e => setSequence(e.target.value.toUpperCase().replace(/[^ACDEFGHIKLMNPQRSTVWY]/g, ''))}
                placeholder="Paste amino-acid sequence…"
              />
              <div className="text-xs text-gray-400 mt-1">{sequence.length} residues</div>
            </div>

            <div className="flex items-center gap-4">
              <div>
                <label className="block text-sm font-semibold mb-1 text-gray-700 dark:text-gray-300">
                  Top-K suggestions
                </label>
                <input
                  type="number" min={1} max={50}
                  value={topK}
                  onChange={e => setTopK(Number(e.target.value))}
                  className="w-24 p-2 border border-gray-300 dark:border-gray-600 rounded-lg
                             bg-white dark:bg-gray-700 text-sm"
                />
              </div>
              <div className="pt-5">
                <RunBtn onClick={handleSuggestMutations} loading={mutLoading} label="Suggest Mutations" />
              </div>
            </div>

            <ErrorBox msg={mutError} />
          </div>

          {llrResults.length > 0 && (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              <MutationHeatmap
                results={llrResults}
                sequence={sequence}
                title="Predicted Mutation Effects"
              />
              <ProteinViewer3D
                sequence={sequence}
                mutationPositions={llrResults.filter(r => r.llr > 0.3).map(r => r.position + 1)}
                title="Sequence with Beneficial Sites"
              />
            </div>
          )}
        </div>
      )}

      {/* ── Tab 2: Pathway Designer ── */}
      {tab === 'pathway' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6 space-y-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              Flux Balance Analysis
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Simulate metabolic flux under gene knockouts or overexpressions.
              Uses COBRApy FBA (demo mode when model file is absent).
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold mb-1 text-gray-700 dark:text-gray-300">
                  Target Reaction ID
                </label>
                <input
                  type="text"
                  placeholder="e.g. EX_etoh_e"
                  className="w-full p-2.5 border border-gray-300 dark:border-gray-600 rounded-lg
                             bg-white dark:bg-gray-700 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  value={targetRxn}
                  onChange={e => setTargetRxn(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1 text-gray-700 dark:text-gray-300">
                  Gene Knockouts (comma-separated)
                </label>
                <input
                  type="text"
                  placeholder="e.g. b0008, b0114"
                  className="w-full p-2.5 border border-gray-300 dark:border-gray-600 rounded-lg
                             bg-white dark:bg-gray-700 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  value={koGenes}
                  onChange={e => setKoGenes(e.target.value)}
                />
              </div>
            </div>

            <RunBtn onClick={handleRunFBA} loading={fluxLoading} label="Run FBA" />
            <ErrorBox msg={fluxError} />
          </div>

          {fluxData && <PathwayMapViewer data={fluxData} />}
        </div>
      )}

      {/* ── Tab 3: Gene Editing ── */}
      {tab === 'editing' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6 space-y-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              CRISPR gRNA Design
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              AI-predicted guide RNA sequences with on-target efficiency and off-target risk scores.
              Integrates CRISPy / DeepCRISTL predictions when available.
            </p>

            <div className="flex flex-wrap gap-4 items-end">
              <div>
                <label className="block text-sm font-semibold mb-1 text-gray-700 dark:text-gray-300">
                  Target Gene
                </label>
                <input
                  type="text"
                  placeholder="e.g. adhE, pykF, zwf"
                  className="w-40 p-2.5 border border-gray-300 dark:border-gray-600 rounded-lg
                             bg-white dark:bg-gray-700 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  value={targetGene}
                  onChange={e => setTargetGene(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1 text-gray-700 dark:text-gray-300">
                  Number of guides
                </label>
                <input
                  type="number" min={1} max={20}
                  className="w-20 p-2.5 border border-gray-300 dark:border-gray-600 rounded-lg
                             bg-white dark:bg-gray-700 text-sm"
                  value={nGuides}
                  onChange={e => setNGuides(Number(e.target.value))}
                />
              </div>
              <RunBtn onClick={handleDesignGrna} loading={grnaLoading} label="Design gRNAs" />
            </div>

            <ErrorBox msg={grnaError} />
          </div>

          {guides.length > 0 && (
            <GeneEditingViewer guides={guides} targetGene={targetGene} />
          )}
        </div>
      )}
    </div>
  )
}
