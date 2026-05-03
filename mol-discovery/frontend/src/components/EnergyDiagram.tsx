'use client'

/**
 * EnergyDiagram
 * -------------
 * Displays a reaction energy profile fetched from the real backend.
 * Shows the NEB path (reactants → TS → products) with:
 *   - Activation energy (Ea) annotation
 *   - Reaction energy (ΔG) annotation
 *   - Calculator badge (demo / ASE-EMT / M3GNet)
 *   - "Compute" button when no data is available yet
 *
 * Props
 * -----
 * candidateId    – catalyst DB id
 * reactionSmiles – reaction SMILES string (R>>P format)
 * catalystName   – display name
 * staticProfile  – optional pre-loaded profile (skips fetch)
 */

import React, { useEffect, useState, useCallback } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, ResponsiveContainer, Label,
} from 'recharts'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface EnergyProfile {
  reactant_energy:         number
  product_energy:          number
  transition_state_energy: number
  activation_energy_eV:    number
  reaction_energy_eV:      number
  neb_energies:            number[]
  reaction_coordinate?:    number[]
  calculator:              string
  cached:                  boolean
  computed_at?:            string
  error?:                  string
}

interface EnergyDiagramProps {
  candidateId?:    string
  reactionSmiles?: string
  catalystName?:   string
  staticProfile?:  EnergyProfile
  title?:          string
  height?:         number
}

// Legacy prop shape (backward compat with old usage)
interface LegacyProps {
  profile?: {
    transition_state_energy: number
    product_energy:          number
    intermediates?:          Record<string, number>
  }
}

function buildChartData(profile: EnergyProfile) {
  const energies = profile.neb_energies
  const coords   = profile.reaction_coordinate ||
    energies.map((_, i) => i / (energies.length - 1))

  return energies.map((e, i) => ({
    coord:  Math.round(coords[i] * 100) / 100,
    energy: Math.round(e * 1000) / 1000,
    label:  i === 0 ? 'Reactants'
          : i === energies.length - 1 ? 'Products'
          : i === energies.indexOf(Math.max(...energies)) ? 'TS'
          : undefined,
  }))
}

function CalcBadge({ calc }: { calc: string }) {
  const color =
    calc === 'M3GNet'  ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300' :
    calc === 'ASE-EMT' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300' :
                         'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${color}`}>
      {calc}
    </span>
  )
}

const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700
                    rounded-lg px-3 py-2 text-sm shadow-lg">
      {d.label && <div className="font-bold text-gray-900 dark:text-white mb-1">{d.label}</div>}
      <div className="text-gray-600 dark:text-gray-400">
        Coord: <strong>{d.coord}</strong>
      </div>
      <div className="text-blue-600 dark:text-blue-400">
        Energy: <strong>{d.energy.toFixed(3)} eV</strong>
      </div>
    </div>
  )
}

export default function EnergyDiagram(props: EnergyDiagramProps & LegacyProps) {
  const {
    candidateId,
    reactionSmiles = 'CCO>>CC=O',
    catalystName   = '',
    staticProfile,
    title          = 'Reaction Energy Profile',
    height         = 360,
    profile: legacyProfile,
  } = props

  const [data, setData]       = useState<EnergyProfile | null>(staticProfile || null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  // Handle legacy static profile prop
  useEffect(() => {
    if (legacyProfile && !staticProfile && !candidateId) {
      const n = 9
      const Ea = legacyProfile.transition_state_energy
      const dG = legacyProfile.product_energy
      const energies = Array.from({ length: n }, (_, i) => {
        const t = i / (n - 1)
        return t === 0 ? 0 : t === 1 ? dG : Ea * Math.exp(-((t - 0.4) ** 2) / 0.02) + dG * t
      })
      setData({
        reactant_energy:         0,
        product_energy:          dG,
        transition_state_energy: Ea,
        activation_energy_eV:    Ea,
        reaction_energy_eV:      dG,
        neb_energies:            energies,
        calculator:              'demo',
        cached:                  false,
      })
    }
  }, [legacyProfile, staticProfile, candidateId])

  const fetchProfile = useCallback(async (force = false) => {
    if (!candidateId) return
    setLoading(true)
    setError('')
    try {
      const params = new URLSearchParams({
        reaction_smiles: reactionSmiles,
        catalyst_name:   catalystName,
        force:           String(force),
      })
      const res = await fetch(
        `${API}/api/energy/${candidateId}/default?${params}`
      )
      if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`)
      setData(await res.json())
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [candidateId, reactionSmiles, catalystName])

  useEffect(() => {
    if (candidateId && !staticProfile) fetchProfile()
  }, [candidateId, staticProfile, fetchProfile])

  // ── Render ──────────────────────────────────────────────────────────

  if (!data && !candidateId && !legacyProfile) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6 text-center text-gray-400">
        No energy profile data. Pass a candidateId or staticProfile.
      </div>
    )
  }

  const chartData = data ? buildChartData(data) : []
  const minE = data ? Math.min(...data.neb_energies) - 0.1 : -1
  const maxE = data ? Math.max(...data.neb_energies) + 0.1 : 2

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white">{title}</h3>
        <div className="flex items-center gap-2">
          {data && <CalcBadge calc={data.calculator} />}
          {data?.cached && (
            <span className="text-xs text-gray-400">cached</span>
          )}
          {candidateId && (
            <button
              onClick={() => fetchProfile(true)}
              disabled={loading}
              className="text-xs px-3 py-1 rounded-lg border border-gray-300 dark:border-gray-600
                         hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Computing…' : 'Recompute'}
            </button>
          )}
        </div>
      </div>

      {/* Key metrics */}
      {data && (
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-orange-50 dark:bg-orange-900/20 rounded-xl p-3">
            <div className="text-xs text-orange-600 dark:text-orange-400 font-semibold">
              Activation Energy (Ea)
            </div>
            <div className="text-xl font-bold text-orange-700 dark:text-orange-300 mt-0.5">
              {data.activation_energy_eV.toFixed(3)} eV
            </div>
          </div>
          <div className={`rounded-xl p-3 ${
            data.reaction_energy_eV < 0
              ? 'bg-green-50 dark:bg-green-900/20'
              : 'bg-red-50 dark:bg-red-900/20'
          }`}>
            <div className={`text-xs font-semibold ${
              data.reaction_energy_eV < 0
                ? 'text-green-600 dark:text-green-400'
                : 'text-red-600 dark:text-red-400'
            }`}>
              Reaction Energy (ΔG)
            </div>
            <div className={`text-xl font-bold mt-0.5 ${
              data.reaction_energy_eV < 0
                ? 'text-green-700 dark:text-green-300'
                : 'text-red-700 dark:text-red-300'
            }`}>
              {data.reaction_energy_eV > 0 ? '+' : ''}{data.reaction_energy_eV.toFixed(3)} eV
            </div>
          </div>
        </div>
      )}

      {/* Loading / error states */}
      {loading && !data && (
        <div className="flex items-center justify-center h-32 text-gray-400 gap-2">
          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          Computing energy profile…
        </div>
      )}

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800
                        rounded-lg px-3 py-2 text-sm text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {/* No data + compute button */}
      {!data && !loading && candidateId && (
        <div className="flex flex-col items-center justify-center h-32 gap-3 text-gray-400">
          <p className="text-sm">No energy profile computed yet.</p>
          <button
            onClick={() => fetchProfile()}
            className="px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white
                       text-sm font-semibold transition-colors"
          >
            Compute Energy Profile
          </button>
        </div>
      )}

      {/* Chart */}
      {data && chartData.length > 0 && (
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={chartData} margin={{ top: 10, right: 20, bottom: 30, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="coord"
              type="number"
              domain={[0, 1]}
              tickCount={5}
            >
              <Label
                value="Reaction Coordinate"
                position="insideBottom"
                offset={-15}
                style={{ fill: '#6b7280', fontSize: 12 }}
              />
            </XAxis>
            <YAxis domain={[minE, maxE]}>
              <Label
                value="Energy (eV)"
                angle={-90}
                position="insideLeft"
                offset={10}
                style={{ fill: '#6b7280', fontSize: 12 }}
              />
            </YAxis>
            <Tooltip content={<CustomTooltip />} />
            {/* Zero reference line */}
            <ReferenceLine y={0} stroke="#9ca3af" strokeDasharray="4 4" />
            {/* TS reference line */}
            <ReferenceLine
              y={data.transition_state_energy}
              stroke="#f97316"
              strokeDasharray="4 4"
              label={{ value: 'TS', fill: '#f97316', fontSize: 11 }}
            />
            <Line
              type="monotone"
              dataKey="energy"
              stroke="#2563eb"
              strokeWidth={2.5}
              dot={(p: any) => {
                const d = p.payload
                if (!d.label) return <circle key={p.key} cx={p.cx} cy={p.cy} r={3} fill="#2563eb" />
                const color = d.label === 'TS' ? '#f97316' :
                              d.label === 'Reactants' ? '#10b981' : '#ef4444'
                return (
                  <g key={p.key}>
                    <circle cx={p.cx} cy={p.cy} r={6} fill={color} />
                    <text x={p.cx} y={p.cy - 10} textAnchor="middle"
                          fontSize={10} fill={color} fontWeight="600">
                      {d.label}
                    </text>
                  </g>
                )
              }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}

      {data?.error && (
        <div className="text-xs text-amber-600 dark:text-amber-400">
          Note: {data.error} (showing demo profile)
        </div>
      )}
    </div>
  )
}
