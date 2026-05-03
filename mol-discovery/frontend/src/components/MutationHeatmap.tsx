'use client'

/**
 * MutationHeatmap
 * ---------------
 * Displays LLR scores for a set of mutations as a colour-coded grid.
 * Rows = amino-acid positions, columns = mutant amino acids.
 * Green = beneficial (positive LLR), red = deleterious (negative LLR).
 *
 * Props
 * -----
 * results  – array returned by POST /api/enzyme/llr or /api/enzyme/suggest
 * sequence – wild-type sequence string (used to label rows)
 * title    – optional card title
 */

import React, { useMemo, useState } from 'react'

export interface LLRResult {
  position:       number   // 0-indexed
  mutation:       string   // e.g. "A42G"
  wt:             string
  mt:             string
  llr:            number
  interpretation: string
}

interface MutationHeatmapProps {
  results:  LLRResult[]
  sequence?: string
  title?:   string
}

// Map LLR → CSS background colour (green positive, red negative)
function llrColor(llr: number): string {
  const clamped = Math.max(-3, Math.min(3, llr))
  if (clamped >= 0) {
    const intensity = Math.round((clamped / 3) * 200)
    return `rgb(${55 - intensity}, ${160 + intensity * 0.3}, ${55 - intensity * 0.2})`
  }
  const intensity = Math.round((Math.abs(clamped) / 3) * 200)
  return `rgb(${160 + intensity * 0.3}, ${55 - intensity}, ${55 - intensity * 0.2})`
}

function llrTextColor(llr: number): string {
  return Math.abs(llr) > 1.2 ? '#fff' : '#1f2937'
}

export default function MutationHeatmap({
  results,
  sequence,
  title = 'Mutation Effect Heatmap',
}: MutationHeatmapProps) {
  const [hovered, setHovered] = useState<LLRResult | null>(null)
  const [sortBy, setSortBy] = useState<'position' | 'llr'>('position')

  const sorted = useMemo(
    () =>
      [...results].sort((a, b) =>
        sortBy === 'position' ? a.position - b.position : b.llr - a.llr
      ),
    [results, sortBy]
  )

  if (!results.length) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6 text-center text-gray-400">
        No mutation data to display.
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white">{title}</h3>
        <div className="flex gap-2 text-xs">
          <button
            onClick={() => setSortBy('position')}
            className={`px-3 py-1 rounded-full border transition-colors ${
              sortBy === 'position'
                ? 'bg-blue-600 text-white border-blue-600'
                : 'border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400'
            }`}
          >
            By position
          </button>
          <button
            onClick={() => setSortBy('llr')}
            className={`px-3 py-1 rounded-full border transition-colors ${
              sortBy === 'llr'
                ? 'bg-blue-600 text-white border-blue-600'
                : 'border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400'
            }`}
          >
            By LLR
          </button>
        </div>
      </div>

      {/* Colour scale legend */}
      <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
        <span>Deleterious</span>
        <div className="flex h-4 rounded overflow-hidden flex-1 max-w-[200px]">
          {[-3, -2, -1, 0, 1, 2, 3].map(v => (
            <div key={v} className="flex-1" style={{ background: llrColor(v) }} />
          ))}
        </div>
        <span>Beneficial</span>
      </div>

      {/* Grid */}
      <div className="overflow-x-auto">
        <div className="flex flex-wrap gap-1.5">
          {sorted.map(r => (
            <div
              key={r.mutation}
              className="relative cursor-pointer rounded-md flex items-center justify-center
                         text-xs font-mono font-semibold transition-transform hover:scale-110
                         w-14 h-10 select-none"
              style={{
                background: llrColor(r.llr),
                color:      llrTextColor(r.llr),
              }}
              onMouseEnter={() => setHovered(r)}
              onMouseLeave={() => setHovered(null)}
            >
              {r.mutation}
            </div>
          ))}
        </div>
      </div>

      {/* Tooltip */}
      {hovered && (
        <div className="bg-gray-900 text-white rounded-xl p-4 text-sm space-y-1">
          <div className="font-bold text-base">{hovered.mutation}</div>
          <div>
            Position <strong>{hovered.position + 1}</strong>: {hovered.wt} → {hovered.mt}
          </div>
          <div>
            LLR: <strong className={hovered.llr >= 0 ? 'text-green-400' : 'text-red-400'}>
              {hovered.llr > 0 ? '+' : ''}{hovered.llr.toFixed(3)}
            </strong>
          </div>
          <div className="text-gray-300 capitalize">{hovered.interpretation}</div>
          {sequence && (
            <div className="text-gray-400 font-mono text-xs mt-1">
              Context: …{sequence.slice(Math.max(0, hovered.position - 3), hovered.position)}
              <span className="text-yellow-300 font-bold">{hovered.wt}</span>
              {sequence.slice(hovered.position + 1, hovered.position + 4)}…
            </div>
          )}
        </div>
      )}

      {/* Summary stats */}
      <div className="grid grid-cols-3 gap-3 pt-2 border-t border-gray-100 dark:border-gray-700">
        {[
          {
            label: 'Beneficial',
            value: results.filter(r => r.llr > 0.3).length,
            color: 'text-green-600',
          },
          {
            label: 'Neutral',
            value: results.filter(r => r.llr >= -0.3 && r.llr <= 0.3).length,
            color: 'text-gray-500',
          },
          {
            label: 'Deleterious',
            value: results.filter(r => r.llr < -0.3).length,
            color: 'text-red-600',
          },
        ].map(({ label, value, color }) => (
          <div key={label} className="text-center">
            <div className={`text-2xl font-bold ${color}`}>{value}</div>
            <div className="text-xs text-gray-500 dark:text-gray-400">{label}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
