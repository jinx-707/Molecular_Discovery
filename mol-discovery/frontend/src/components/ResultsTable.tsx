'use client'

import React, { useState } from 'react'
import type { Candidate } from '@/services/api'

interface ResultsTableProps {
  data: Candidate[]
  onSelect?: (c: Candidate) => void
}

type SortKey = 'score' | 'predicted_activity' | 'predicted_selectivity' | 'predicted_stability'

const ResultsTable: React.FC<ResultsTableProps> = ({ data, onSelect }) => {
  const [sortBy, setSortBy]   = useState<SortKey>('score')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')

  const handleSort = (col: SortKey) => {
    if (sortBy === col) setSortDir(d => (d === 'asc' ? 'desc' : 'asc'))
    else { setSortBy(col); setSortDir('desc') }
  }

  const sorted = [...data].sort((a, b) => {
    const av = a[sortBy] as number
    const bv = b[sortBy] as number
    return sortDir === 'asc' ? av - bv : bv - av
  })

  const SortIcon = ({ col }: { col: SortKey }) =>
    sortBy === col ? (
      <span>{sortDir === 'desc' ? ' ↓' : ' ↑'}</span>
    ) : (
      <span className="opacity-30"> ↕</span>
    )

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-x-auto">
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
              Selectivity <SortIcon col="predicted_selectivity" />
            </th>
            <th
              className="px-4 py-3 text-left font-semibold cursor-pointer hover:text-blue-600"
              onClick={() => handleSort('predicted_stability')}
            >
              Stability <SortIcon col="predicted_stability" />
            </th>
            <th className="px-4 py-3 text-left font-semibold">Uncertainty</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((c, i) => (
            <tr
              key={c.id}
              onClick={() => onSelect?.(c)}
              className="border-t border-gray-100 dark:border-gray-700
                         hover:bg-blue-50 dark:hover:bg-blue-900/20 cursor-pointer transition-colors"
            >
              <td className="px-4 py-3 text-gray-400 font-mono">{i + 1}</td>
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                      c.type === 'novel'
                        ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
                        : 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                    }`}
                  >
                    {c.type}
                  </span>
                  <span className="font-medium text-gray-900 dark:text-white truncate max-w-[180px]">
                    {c.name}
                  </span>
                </div>
              </td>
              <td className="px-4 py-3 font-mono font-semibold">{c.score.toFixed(3)}</td>
              <td className="px-4 py-3 font-mono">{c.predicted_activity.toFixed(2)}</td>
              <td className="px-4 py-3 font-mono">{(c.predicted_selectivity * 100).toFixed(1)}%</td>
              <td className="px-4 py-3 font-mono">{c.predicted_stability} h</td>
              <td className="px-4 py-3 font-mono text-gray-400">
                ±{(c.uncertainty * 100).toFixed(0)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default ResultsTable
