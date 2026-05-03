'use client'

import React from 'react'
import Link from 'next/link'

export default function Home() {

  return (
    <div className="max-w-6xl mx-auto py-14 px-4 space-y-16">
      {/* ── Hero ── */}
      <div className="text-center space-y-6">
        <h1 className="text-5xl sm:text-6xl font-extrabold bg-gradient-to-r from-purple-600 to-blue-600
                        bg-clip-text text-transparent">
          MolDiscovery
        </h1>
        <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
          AI-powered catalyst screening platform. Screen thousands of candidates in minutes,
          log lab results, and let the model learn from your data.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/discovery"
            className="px-8 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white
                       font-semibold text-lg transition-colors shadow-md"
          >
            Start Discovery
          </Link>
          <Link
            href="/experiments"
            className="px-8 py-3 rounded-xl border-2 border-gray-300 dark:border-gray-600
                       hover:bg-gray-50 dark:hover:bg-gray-800 font-semibold text-lg transition-colors"
          >
            Log Experiments
          </Link>
        </div>
      </div>



      {/* ── Feature cards ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          {
            icon: '⚡',
            title: 'Instant Screening',
            desc: 'AI predicts activity, selectivity, and stability for 20+ candidates in seconds.',
            href: '/discovery' as const,
            cta: 'Start Discovery',
          },
          {
            icon: '🔬',
            title: 'Experiment Logging',
            desc: 'Log lab results via form or CSV. Platform auto-detects prediction discrepancies.',
            href: '/experiments' as const,
            cta: 'Log Results',
          },
          {
            icon: '📈',
            title: 'Active Learning',
            desc: 'Model fine-tunes on your data. Accuracy improves with every experiment logged.',
            href: '/models' as const,
            cta: 'View Model Health',
          },
        ].map(({ icon, title, desc, href, cta }) => (
          <div
            key={title}
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-7 flex flex-col"
          >
            <div className="text-4xl mb-3">{icon}</div>
            <h3 className="text-lg font-bold mb-2 text-gray-900 dark:text-white">{title}</h3>
            <p className="text-gray-500 dark:text-gray-400 text-sm flex-1">{desc}</p>
            <Link
              href={href}
              className="mt-5 text-sm font-semibold text-blue-600 dark:text-blue-400 hover:underline"
            >
              {cta} →
            </Link>
          </div>
        ))}
      </div>

      {/* ── Workflow ── */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-8">
        <h2 className="text-2xl font-bold mb-6 text-gray-900 dark:text-white">How It Works</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {[
            {
              step: '1',
              title: 'Enter Reaction',
              desc: 'Type your target reaction (e.g. "ethanol to jet fuel"). The platform retrieves known catalysts and generates novel AI candidates.',
            },
            {
              step: '2',
              title: 'Review Predictions',
              desc: 'Candidates are ranked by a composite score (activity 40%, selectivity 30%, stability 20%, uncertainty −10%). Export to CSV.',
            },
            {
              step: '3',
              title: 'Close the Loop',
              desc: 'Log your lab measurements. The platform flags discrepancies and fine-tunes the model on your real data.',
            },
          ].map(({ step, title, desc }) => (
            <div key={step} className="flex gap-4">
              <div className="flex-shrink-0 w-9 h-9 rounded-full bg-blue-600 text-white
                              flex items-center justify-center font-bold text-sm">
                {step}
              </div>
              <div>
                <div className="font-semibold text-gray-900 dark:text-white mb-1">{title}</div>
                <div className="text-sm text-gray-500 dark:text-gray-400">{desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>


    </div>
  )
}
