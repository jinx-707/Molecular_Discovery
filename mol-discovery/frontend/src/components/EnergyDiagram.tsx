'use client'

import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface EnergyDiagramProps {
  profile: {
    transition_state_energy: number;
    product_energy: number;
    intermediates: { [key: string]: number };
  };
}

const EnergyDiagram: React.FC<EnergyDiagramProps> = ({ profile }) => {
  const data = [
    { name: 'Reactants', energy: 0 },
    { name: 'TS', energy: profile.transition_state_energy },
    { name: 'IM1', energy: profile.intermediates.IM1 || 0.6 },
    { name: 'IM2', energy: profile.intermediates.IM2 || 0.8 },
    { name: 'Products', energy: profile.product_energy }
  ];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
      <h3 className="font-bold mb-4 text-xl">Energy Profile</h3>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" label={{ value: 'Reaction Coordinate', position: 'insideBottom', offset: -5 }} />
          <YAxis label={{ value: 'Free Energy (kcal/mol)', angle: -90, position: 'insideLeft' }} />
          <Tooltip />
          <Line type="monotone" dataKey="energy" stroke="#2563eb" strokeWidth={3} dot={{ r: 6 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default EnergyDiagram;

