'use client'

import React from 'react';

interface Candidate {
  id: string;
  smiles: string;
  activity: number;
  selectivity: number;
  stability: number;
  uncertainty: number;
  score: number;
}

interface ResultsTableProps {
  data: Candidate[];
}

const ResultsTable: React.FC<ResultsTableProps> = ({ data }) => {
  const [sortBy, setSortBy] = React.useState<'score' | 'activity' | 'selectivity'>('score');
  const [sortDir, setSortDir] = React.useState<'asc' | 'desc'>('desc');

  const sortedData = [...data].sort((a, b) => {
    const aVal = a[sortBy];
    const bVal = b[sortBy];
    if (sortDir === 'asc') {
      return aVal - bVal;
    } else {
      return bVal - aVal;
    }
  });

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="bg-gray-50 dark:bg-gray-700">
            <th className="p-4 text-left font-medium cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600" onClick={() => {setSortBy('score'); setSortDir(sortDir === 'desc' ? 'asc' : 'desc');}}>
              Score <span>{sortBy === 'score' ? (sortDir === 'desc' ? '↓' : '↑') : ''}</span>
            </th>
            <th className="p-4 text-left font-medium cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600" onClick={() => {setSortBy('activity'); setSortDir(sortDir === 'desc' ? 'asc' : 'desc');}}>
              Activity
            </th>
            <th className="p-4 text-left font-medium">Selectivity</th>
            <th className="p-4 text-left font-medium">Stability</th>
            <th className="p-4 text-left font-medium">Uncertainty</th>
            <th className="p-4 text-left font-medium">Structure</th>
          </tr>
        </thead>
        <tbody>
          {sortedData.slice(0, 10).map((candidate) => (
            <tr key={candidate.id} className="border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer">
              <td className="p-4 font-mono">{candidate.score.toFixed(3)}</td>
              <td className="p-4">{candidate.activity.toFixed(2)}</td>
              <td className="p-4">{candidate.selectivity.toFixed(2)}</td>
              <td className="p-4">{candidate.stability.toFixed(1)}h</td>
              <td className="p-4">{candidate.uncertainty.toFixed(3)}</td>
              <td className="p-4">
                <span className="text-blue-600 dark:text-blue-400 hover:underline">3D View</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ResultsTable;

