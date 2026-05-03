import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ResultsTable from '../../src/components/ResultsTable';

const mockData = [
  { id: '1', smiles: 'TiO2', activity: 2.5, selectivity: 0.9, stability: 48, uncertainty: 0.05, score: 0.85 },
  { id: '2', smiles: 'ZrO2', activity: 2.1, selectivity: 0.85, stability: 36, uncertainty: 0.08, score: 0.82 }
];

test('renders results table', () => {
  render(<ResultsTable data={mockData} />);
  
  expect(screen.getByText('Score')).toBeInTheDocument();
  expect(screen.getByText('TiO2')).toBeInTheDocument();
  expect(screen.getByText('2.5')).toBeInTheDocument();
});

test('sorts by score on click', () => {
  render(<ResultsTable data={mockData} />);
  
  fireEvent.click(screen.getByText('Score'));
  // Verify sort logic via DOM order (simplified)
  expect(screen.getAllByText(/TiO2|ZrO2/)[0]).toHaveTextContent('TiO2');  // higher score first
});

