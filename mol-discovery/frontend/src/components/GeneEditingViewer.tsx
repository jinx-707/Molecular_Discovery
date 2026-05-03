'use client'

/**
 * GeneEditingViewer
 * -----------------
 * Displays CRISPR gRNA candidates for a target gene.
 * Shows on-target score, off-target score, GC content, and sequence.
 *
 * Props
 * -----
 * guides      – array returned by POST /api/enzyme/grna
 * targetGene  – gene name (for display)
 * onSelect    – optional callback when a guide is selected
 */

import React, { useState } from 'react'

export interface GuideRNA {
  rank:             number
  sequence:         string
  pam:              string
  on_target_score:  number
  off_target_score: number
  gc_content:       number
  target_gene:      string
  position:         number
}

interface GeneEditingViewerProps {
  guides:     GuideRNA[]
  targetGene: string
  onSelect?:  (guide: GuideRNA) => void
  title?:     string
}

function ScoreGauge({
  value,
  label,
  good = 'high',
}: {
  value: number
  label: string
  good?: 'high' | 'low'
}) {
  const pct = Math.round(value * 100)
  const isGood = good === 'high' ? value >= 0.7 : value <= 0.1
  const isMid  = good === 'high' ? value >= 0.5 : value <= 0.2
  const color  = isGood ? 'bg-green-500' : isMid ? 'bg-yellow-500' : 'bg-red-400'

  return (
    <div className="space-y-0.5">
      <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
        <span>{label}</span>
        <span className="font-semibold text-gray-900 dark:text-white">{pct}%</span>
      </div>
      <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
        <div className={`${color} h-1.5 rounded-full`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

function NucleotideSeq({ seq, pam }: { seq: string; pam: string }) {
  const colors: Record<string, string> = {
    A: 'text-green-600 dark:text-green-400',
    T: 'text-red-600 dark:text-red-400',
    G: 'text-yellow-600 dark:text-yellow-400',
    C: 'text-blue-600 dark:text-blue-400',
  }
  return (
    <span className="font-mono text-sm tracking-wider">
      {seq.split('').map((c, i) => (
        <span key={i} className={colors[c] ?? 'text-gray-600'}>
          {c}
        </span>
      ))}
      <span className="text-gray-400 ml-1">{pam}</span>
    </span>
  )
}

export default function GeneEditingViewer({
  guides,
  targetGene,
  onSelect,
  title = 'CRISPR gRNA Design',
}: GeneEditingViewerProps) {
  const [selected, setSelected] = useState<number | null>(null)
  const [copied, setCopied]     = useState<number | null>(null)

  const handleSelect = (guide: GuideRNA) => {
    setSelected(guide.rank)
    onSelect?.(guide)
  }

  const handleCopy = (guide: GuideRNA, e: React.MouseEvent) => {
    e.stopPropagation()
    navigator.clipboard.writeText(guide.sequence + guide.pam).catch(() => {})
    setCopied(guide.rank)
    setTimeout(() => setCopied(null), 1500)
  }

  if (!guides.length) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6 text-center text-gray-400">
        No gRNA guides available.
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6 space-y-4">
      {/* Header */}
      <div>
        <h3 className="text-lg font-bold text-gray-900 dark:text-white">{title}</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
          Target gene: <strong className="text-gray-900 dark:text-white">{targetGene}</strong>
          {' · '}{guides.length} guide RNAs ranked by on-target efficiency
        </p>
      </div>

      {/* Guide list */}
      <div className="space-y-3">
        {guides.map(guide => (
          <div
            key={guide.rank}
            onClick={() => handleSelect(guide)}
            className={`rounded-xl border-2 p-4 cursor-pointer transition-all ${
              selected === guide.rank
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-600'
            }`}
          >
            <div className="flex items-start justify-between gap-3 mb-3">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-blue-600 text-white text-xs
                                 flex items-center justify-center font-bold flex-shrink-0">
                  {guide.rank}
                </span>
                <NucleotideSeq seq={guide.sequence} pam={guide.pam} />
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <span className="text-xs text-gray-400">pos {guide.position}</span>
                <button
                  onClick={e => handleCopy(guide, e)}
                  className="text-xs px-2 py-1 rounded border border-gray-300 dark:border-gray-600
                             hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  {copied === guide.rank ? 'Copied!' : 'Copy'}
                </button>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <ScoreGauge
                value={guide.on_target_score}
                label="On-target"
                good="high"
              />
              <ScoreGauge
                value={guide.off_target_score}
                label="Off-target"
                good="low"
              />
              <ScoreGauge
                value={guide.gc_content}
                label="GC content"
                good="high"
              />
            </div>
          </div>
        ))}
      </div>

      {/* Selected guide detail */}
      {selected !== null && (
        <div className="bg-gray-50 dark:bg-gray-700 rounded-xl p-4 text-sm space-y-2">
          {(() => {
            const g = guides.find(g => g.rank === selected)!
            return (
              <>
                <div className="font-semibold text-gray-900 dark:text-white">
                  Guide #{g.rank} selected
                </div>
                <div className="grid grid-cols-2 gap-2 text-gray-600 dark:text-gray-300">
                  <div>Sequence: <code className="font-mono">{g.sequence}</code></div>
                  <div>PAM: <code className="font-mono">{g.pam}</code></div>
                  <div>On-target: <strong>{(g.on_target_score * 100).toFixed(1)}%</strong></div>
                  <div>Off-target: <strong>{(g.off_target_score * 100).toFixed(1)}%</strong></div>
                </div>
                <div className="text-xs text-gray-400">
                  Recommendation:{' '}
                  {g.on_target_score >= 0.8 && g.off_target_score <= 0.05
                    ? 'Excellent candidate — high efficiency, minimal off-target risk.'
                    : g.on_target_score >= 0.65
                    ? 'Good candidate — validate off-target sites before use.'
                    : 'Moderate efficiency — consider higher-ranked alternatives.'}
                </div>
              </>
            )
          })()}
        </div>
      )}
    </div>
  )
}
