'use client'

/**
 * ProteinViewer3D
 * ---------------
 * Interactive 3D protein structure viewer using NGL Viewer.
 * Highlights mutation positions in red on the structure.
 *
 * Falls back to a sequence-based 2D representation when NGL is not
 * available (e.g. SSR, missing npm package).
 *
 * Install NGL:  npm install ngl
 *
 * Props
 * -----
 * pdbData         – PDB file content as a string, OR
 * pdbId           – RCSB PDB accession (e.g. "1TIM") to load remotely
 * mutationPositions – 1-indexed positions to highlight in red
 * sequence        – amino-acid sequence for the fallback 2D view
 * title           – optional card title
 */

import React, { useEffect, useRef, useState } from 'react'

export interface ProteinViewer3DProps {
  pdbData?:           string
  pdbId?:             string
  mutationPositions?: number[]   // 1-indexed
  sequence?:          string
  title?:             string
  height?:            number
}

// ---------------------------------------------------------------------------
// 2-D sequence fallback (always works, no external deps)
// ---------------------------------------------------------------------------

function SequenceFallback({
  sequence,
  mutationPositions = [],
  title,
}: {
  sequence: string
  mutationPositions?: number[]
  title?: string
}) {
  const mutSet = new Set(mutationPositions)
  const CHUNK  = 10

  const chunks: string[][] = []
  for (let i = 0; i < sequence.length; i += CHUNK) {
    chunks.push(sequence.slice(i, i + CHUNK).split(''))
  }

  return (
    <div className="space-y-3">
      {title && (
        <h3 className="text-lg font-bold text-gray-900 dark:text-white">{title}</h3>
      )}
      <p className="text-xs text-gray-500 dark:text-gray-400">
        Sequence view (install <code>ngl</code> for 3D rendering)
      </p>
      <div className="font-mono text-sm space-y-1 overflow-x-auto">
        {chunks.map((chunk, ci) => {
          const startPos = ci * CHUNK + 1
          return (
            <div key={ci} className="flex items-center gap-2">
              <span className="text-gray-400 w-8 text-right text-xs">{startPos}</span>
              <span className="flex gap-0.5">
                {chunk.map((aa, j) => {
                  const pos = startPos + j
                  const isMut = mutSet.has(pos)
                  return (
                    <span
                      key={j}
                      title={`${aa}${pos}`}
                      className={`w-5 h-6 flex items-center justify-center rounded text-xs font-bold
                                  ${isMut
                                    ? 'bg-red-500 text-white ring-2 ring-red-300'
                                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                                  }`}
                    >
                      {aa}
                    </span>
                  )
                })}
              </span>
            </div>
          )
        })}
      </div>
      {mutationPositions.length > 0 && (
        <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
          <span className="w-4 h-4 bg-red-500 rounded inline-block" />
          Mutation sites ({mutationPositions.length})
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// NGL 3D viewer
// ---------------------------------------------------------------------------

function NglViewer({
  pdbData,
  pdbId,
  mutationPositions = [],
  height = 400,
}: {
  pdbData?:           string
  pdbId?:             string
  mutationPositions?: number[]
  height?:            number
}) {
  const containerRef = useRef<HTMLDivElement>(null)
  const stageRef     = useRef<any>(null)

  useEffect(() => {
    if (!containerRef.current) return

    let stage: any = null

    const init = async () => {
      try {
        const NGL = await import('ngl' as any)
        stage = new NGL.Stage(containerRef.current, { backgroundColor: '#1e293b' })
        stageRef.current = stage

        let component: any

        if (pdbData) {
          const blob = new Blob([pdbData], { type: 'text/plain' })
          component  = await stage.loadFile(blob, { ext: 'pdb' })
        } else if (pdbId) {
          component = await stage.loadFile(`rcsb://${pdbId}`)
        } else {
          return
        }

        // Base cartoon representation
        component.addRepresentation('cartoon', {
          colorScheme: 'chainname',
          opacity:     0.9,
        })

        // Highlight mutation positions in red
        if (mutationPositions.length > 0) {
          const selStr = mutationPositions.map(p => `${p}`).join(' or ')
          component.addRepresentation('ball+stick', {
            sele:        selStr,
            colorValue:  '#ef4444',
            radiusScale: 1.5,
          })
          component.addRepresentation('surface', {
            sele:        selStr,
            colorValue:  '#ef4444',
            opacity:     0.4,
          })
        }

        component.autoView()
      } catch (err) {
        console.warn('NGL init failed:', err)
      }
    }

    init()

    return () => {
      if (stageRef.current) {
        stageRef.current.dispose()
        stageRef.current = null
      }
    }
  }, [pdbData, pdbId, mutationPositions])

  return (
    <div
      ref={containerRef}
      style={{ height, width: '100%' }}
      className="rounded-xl overflow-hidden bg-slate-800"
    />
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function ProteinViewer3D({
  pdbData,
  pdbId,
  mutationPositions = [],
  sequence,
  title = 'Protein Structure',
  height = 400,
}: ProteinViewer3DProps) {
  const [nglAvailable, setNglAvailable] = useState<boolean | null>(null)
  const [view, setView] = useState<'3d' | '2d'>('3d')

  useEffect(() => {
    import('ngl' as any)
      .then(() => setNglAvailable(true))
      .catch(() => setNglAvailable(false))
  }, [])

  const hasPdb = !!(pdbData || pdbId)

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white">{title}</h3>
        <div className="flex gap-2 text-xs">
          {hasPdb && nglAvailable && (
            <>
              <button
                onClick={() => setView('3d')}
                className={`px-3 py-1 rounded-full border transition-colors ${
                  view === '3d'
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400'
                }`}
              >
                3D
              </button>
              <button
                onClick={() => setView('2d')}
                className={`px-3 py-1 rounded-full border transition-colors ${
                  view === '2d'
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400'
                }`}
              >
                Sequence
              </button>
            </>
          )}
          {mutationPositions.length > 0 && (
            <span className="px-2 py-0.5 bg-red-100 dark:bg-red-900/30
                             text-red-700 dark:text-red-300 rounded-full">
              {mutationPositions.length} mutation{mutationPositions.length > 1 ? 's' : ''} highlighted
            </span>
          )}
        </div>
      </div>

      {/* Viewer */}
      {nglAvailable === null && (
        <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
          Loading viewer…
        </div>
      )}

      {nglAvailable === true && hasPdb && view === '3d' && (
        <NglViewer
          pdbData={pdbData}
          pdbId={pdbId}
          mutationPositions={mutationPositions}
          height={height}
        />
      )}

      {(nglAvailable === false || !hasPdb || view === '2d') && sequence && (
        <SequenceFallback
          sequence={sequence}
          mutationPositions={mutationPositions}
        />
      )}

      {nglAvailable === false && !sequence && (
        <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200
                        dark:border-amber-700 rounded-xl p-4 text-sm text-amber-800
                        dark:text-amber-200">
          <strong>NGL not installed.</strong> Run{' '}
          <code className="bg-amber-100 dark:bg-amber-900 px-1 rounded">npm install ngl</code>{' '}
          to enable 3D rendering, or pass a <code>sequence</code> prop for the 2D view.
        </div>
      )}

      {/* Mutation legend */}
      {mutationPositions.length > 0 && (
        <div className="flex flex-wrap gap-2 pt-2 border-t border-gray-100 dark:border-gray-700">
          <span className="text-xs text-gray-500 dark:text-gray-400">Mutation sites:</span>
          {mutationPositions.slice(0, 12).map(p => (
            <span
              key={p}
              className="text-xs px-2 py-0.5 bg-red-100 dark:bg-red-900/30
                         text-red-700 dark:text-red-300 rounded-full font-mono"
            >
              {p}
            </span>
          ))}
          {mutationPositions.length > 12 && (
            <span className="text-xs text-gray-400">+{mutationPositions.length - 12} more</span>
          )}
        </div>
      )}
    </div>
  )
}
