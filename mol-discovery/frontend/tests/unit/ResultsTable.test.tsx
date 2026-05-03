import React from 'react'
import { render, screen } from '@testing-library/react'
import ResultsTable from '../../src/components/ResultsTable'
import type { Candidate } from '../../src/services/api'

const mockCandidates: Candidate[] = [
  {
    id:                    'c1',
    name:                  'H-ZSM-5 (Si/Al=25)',
    type:                  'known',
    predicted_activity:    1.8,
    predicted_selectivity: 0.82,
    predicted_stability:   340,
    uncertainty:           0.10,
    score:                 0.712,
    details:               'Literature zeolite',
  },
  {
    id:                    'c2',
    name:                  'ZSM-5 with Ga substitution',
    type:                  'novel',
    predicted_activity:    2.4,
    predicted_selectivity: 0.88,
    predicted_stability:   520,
    uncertainty:           0.12,
    score:                 0.851,
    details:               'AI-generated candidate',
    novelty_score:         0.78,
  },
]

test('renders candidate names', () => {
  render(<ResultsTable data={mockCandidates} />)
  expect(screen.getByText('H-ZSM-5 (Si/Al=25)')).toBeTruthy()
  expect(screen.getByText('ZSM-5 with Ga substitution')).toBeTruthy()
})

test('renders type badges', () => {
  render(<ResultsTable data={mockCandidates} />)
  expect(screen.getByText('known')).toBeTruthy()
  expect(screen.getByText('novel')).toBeTruthy()
})
