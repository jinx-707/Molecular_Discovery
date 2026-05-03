'use client'

import React from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ZAxis } from 'recharts';

interface PerformancePlotProps {
  data: Array<{
    activity: number;
    selectivity: number;
    stability: number;
    uncertainty: number;
    name: string;
  }>;
}

const PerformancePlot: React.FC<PerformancePlotProps> = ({ data }) => {
  const chartData = data.map(d => ({
    x: d.activity,
    y: d.selectivity,
    z: d.stability * 100,
    name: d.name,
    uncertainty: d.uncertainty
  }));

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
      <h3 className="font-bold mb-4 text-xl">Performance Scatter</h3>
      <ResponsiveContainer width="100%" height={400}>
        <ScatterChart>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            type="number" 
            dataKey="x" 
            name="Activity" 
            label={{ value: 'Activity (mol/g/h)', position: 'insideBottom', offset: -5 }} 
          />
          <YAxis 
            type="number" 
            dataKey="y" 
            name="Selectivity" 
            label={{ value: 'Selectivity', angle: -90, position: 'insideLeft' }} 
          />
          <ZAxis type="number" dataKey="z" range={[50, 400]} />
          <Tooltip 
            cursor={{ strokeDasharray: '3 3' }}
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-white dark:bg-gray-800 p-3 border border-gray-300 dark:border-gray-600 rounded shadow-lg">
                    <p className="font-semibold">{data.name}</p>
                    <p>Activity: {data.x.toFixed(2)}</p>
                    <p>Selectivity: {data.y.toFixed(2)}</p>
                    <p>Stability: {(data.z / 100).toFixed(1)}h</p>
                    <p>Uncertainty: {data.uncertainty.toFixed(3)}</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Scatter data={chartData} fill="#2563eb" />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PerformancePlot;

