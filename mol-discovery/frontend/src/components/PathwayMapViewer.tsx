'use client'

/**
 * PathwayMapViewer
 * ----------------
 * Visualises metabolic flux as a node-link diagram.
 * Nodes = reactions, edges = metabolite connections.
 * Node size and colour encode flux magnitude.
 *
 * Uses pure SVG — no external graph library required.
 *
 * Props
 * -----
 * fluxes      – Record<reactionId, fluxValue> from POST /api/enzyme/flux
 * knockouts   – list of knocked-out gene IDs (shown in red)
 * title       – optional card title
 */

import React, { useMemo, useState } from 'react'

export interface FluxData {
  status:          string
  growth_rate:     number
  fluxes:          Record<string, number>
  knockouts?:      string[]
  overexpressions?: string[]
  bottlenecks?:    string[]
  demo?:           boolean
}

interface PathwayMapViewerProps {
  data:   FluxData
  title?: string
}

// Fixed layout positions for a simplified central-metabolism map
const LAYOUT: Record<string, [number, number]> = {
  PFK:     [200, 80],
  PGI:     [120, 80],
  PGK:     [280, 80],
  PGM:     [360, 80],
  PYK:     [440, 80],
  CS:      [200, 200],
  ACONTa:  [280, 200],
  ICDHyr:  [360, 200],
  AKGDH:   [440, 200],
  SUCOAS:  [520, 200],
  FUM:     [520, 300],
  MDH:     [440, 300],
  PDH:     [120, 200],
  PPC:     [120, 300],
  PPCK:    [200, 300],
}

const EDGES: [string, string][] = [
  ['PGI', 'PFK'], ['PFK', 'PGK'], ['PGK', 'PGM'], ['PGM', 'PYK'],
  ['PYK', 'PDH'], ['PDH', 'CS'],  ['CS', 'ACONTa'], ['ACONTa', 'ICDHyr'],
  ['ICDHyr', 'AKGDH'], ['AKGDH', 'SUCOAS'], ['SUCOAS', 'FUM'],
  ['FUM', 'MDH'], ['MDH', 'PPCK'], ['PPCK', 'PPC'], ['PPC', 'CS'],
]

function fluxColor(flux: number, max: number, isKnockout: boolean): string {
  if (isKnockout) return '#ef4444'
  const norm = Math.min(1, flux / (max || 1))
  const r = Math.round(59  + (norm * 100))
  const g = Math.round(130 + (norm * 80))
  const b = Math.round(246 - (norm * 150))
  return `rgb(${r},${g},${b})`
}

export default function PathwayMapViewer({
  data,
  title = 'Metabolic Flux Map',
}: PathwayMapViewerProps) {
  const [hovered, setHovered] = useState<string | null>(null)

  const maxFlux = useMemo(
    () => Math.max(1, ...Object.values(data.fluxes)),
    [data.fluxes]
  )

  const knockoutSet = new Set(data.knockouts ?? [])

  // Reactions present in both layout and flux data
  const nodes = Object.entries(LAYOUT).map(([id, [x, y]]) => ({
    id,
    x,
    y,
    flux:       data.fluxes[id] ?? 0,
    isKnockout: knockoutSet.has(id),
  }))

  const nodeMap = Object.fromEntries(nodes.map(n => [n.id, n]))

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white">{title}</h3>
        <div className="flex gap-3 text-xs text-gray-500 dark:text-gray-400">
          <span>
            Growth rate:{' '}
            <strong className="text-gray-900 dark:text-white">
              {data.growth_rate.toFixed(4)} h⁻¹
            </strong>
          </span>
          {data.demo && (
            <span className="px-2 py-0.5 bg-yellow-100 dark:bg-yellow-900/30
                             text-yellow-700 dark:text-yellow-300 rounded-full">
              demo
            </span>
          )}
        </div>
      </div>

      {/* SVG map */}
      <div className="overflow-x-auto">
        <svg
          viewBox="0 0 660 400"
          className="w-full max-w-2xl mx-auto"
          style={{ minWidth: 400 }}
        >
          {/* Edges */}
          {EDGES.map(([a, b]) => {
            const na = nodeMap[a]
            const nb = nodeMap[b]
            if (!na || !nb) return null
            const avgFlux = ((na.flux + nb.flux) / 2)
            const strokeW = Math.max(1, Math.min(6, (avgFlux / maxFlux) * 6))
            return (
              <line
                key={`${a}-${b}`}
                x1={na.x} y1={na.y}
                x2={nb.x} y2={nb.y}
                stroke="#94a3b8"
                strokeWidth={strokeW}
                strokeOpacity={0.6}
              />
            )
          })}

          {/* Nodes */}
          {nodes.map(n => {
            const r     = Math.max(18, Math.min(32, 18 + (n.flux / maxFlux) * 14))
            const color = fluxColor(n.flux, maxFlux, n.isKnockout)
            const isHov = hovered === n.id
            return (
              <g
                key={n.id}
                transform={`translate(${n.x},${n.y})`}
                className="cursor-pointer"
                onMouseEnter={() => setHovered(n.id)}
                onMouseLeave={() => setHovered(null)}
              >
                <circle
                  r={isHov ? r + 4 : r}
                  fill={color}
                  stroke={isHov ? '#1d4ed8' : '#fff'}
                  strokeWidth={isHov ? 3 : 1.5}
                  style={{ transition: 'r 0.15s' }}
                />
                <text
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fontSize={9}
                  fontWeight="600"
                  fill="#fff"
                  style={{ pointerEvents: 'none', userSelect: 'none' }}
                >
                  {n.id}
                </text>
                {n.isKnockout && (
                  <text
                    y={r + 10}
                    textAnchor="middle"
                    fontSize={8}
                    fill="#ef4444"
                    fontWeight="700"
                  >
                    KO
                  </text>
                )}
              </g>
            )
          })}
        </svg>
      </div>

      {/* Tooltip */}
      {hovered && nodeMap[hovered] && (
        <div className="bg-gray-900 text-white rounded-xl p-3 text-sm">
          <span className="font-bold">{hovered}</span>
          {' — '}
          flux: <strong>{(nodeMap[hovered].flux).toFixed(2)} mmol/gDW/h</strong>
          {nodeMap[hovered].isKnockout && (
            <span className="ml-2 text-red-400 font-semibold">knocked out</span>
          )}
        </div>
      )}

      {/* Bottlenecks */}
      {data.bottlenecks && data.bottlenecks.length > 0 && (
        <div className="flex flex-wrap gap-2 pt-2 border-t border-gray-100 dark:border-gray-700">
          <span className="text-xs text-gray-500 dark:text-gray-400">Bottlenecks:</span>
          {data.bottlenecks.map(b => (
            <span
              key={b}
              className="text-xs px-2 py-0.5 bg-orange-100 dark:bg-orange-900/30
                         text-orange-700 dark:text-orange-300 rounded-full"
            >
              {b}
            </span>
          ))}
        </div>
      )}

      {/* Legend */}
      <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
        <span>Low flux</span>
        <div className="flex h-3 rounded overflow-hidden flex-1 max-w-[160px]">
          {[0, 0.25, 0.5, 0.75, 1].map(v => (
            <div key={v} className="flex-1" style={{ background: fluxColor(v * maxFlux, maxFlux, false) }} />
          ))}
        </div>
        <span>High flux</span>
        <span className="ml-2 flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-red-500 inline-block" /> Knockout
        </span>
      </div>
    </div>
  )
}
