'use client'

import React from 'react'
import Link from 'next/link'
import { useT } from '@/lib/i18n'

export default function Home() {
  const t = useT()

  const features = [
    {
      icon: '⚡',
      title: t('home.feature_screening_title'),
      desc:  t('home.feature_screening_desc'),
      href:  '/discovery' as const,
      cta:   t('home.feature_screening_cta'),
    },
    {
      icon: '🔬',
      title: t('home.feature_logging_title'),
      desc:  t('home.feature_logging_desc'),
      href:  '/experiments' as const,
      cta:   t('home.feature_logging_cta'),
    },
    {
      icon: '📈',
      title: t('home.feature_learning_title'),
      desc:  t('home.feature_learning_desc'),
      href:  '/models' as const,
      cta:   t('home.feature_learning_cta'),
    },
  ]

  const steps = [
    { step: '1', title: t('home.step1_title'), desc: t('home.step1_desc') },
    { step: '2', title: t('home.step2_title'), desc: t('home.step2_desc') },
    { step: '3', title: t('home.step3_title'), desc: t('home.step3_desc') },
  ]

  return (
    <div className="max-w-6xl mx-auto py-14 px-4 space-y-16">
      {/* ── Hero ── */}
      <div className="text-center space-y-6">
        <h1 className="text-5xl sm:text-6xl font-extrabold bg-gradient-to-r from-purple-600 to-blue-600
                        bg-clip-text text-transparent">
          {t('home.hero_title')}
        </h1>
        <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
          {t('home.hero_subtitle')}
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/discovery"
            className="px-8 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white
                       font-semibold text-lg transition-colors shadow-md"
          >
            {t('home.cta_discovery')}
          </Link>
          <Link
            href="/experiments"
            className="px-8 py-3 rounded-xl border-2 border-gray-300 dark:border-gray-600
                       hover:bg-gray-50 dark:hover:bg-gray-800 font-semibold text-lg transition-colors"
          >
            {t('home.cta_experiments')}
          </Link>
        </div>
      </div>

      {/* ── Feature cards ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {features.map(({ icon, title, desc, href, cta }) => (
          <div key={title} className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-7 flex flex-col">
            <div className="text-4xl mb-3">{icon}</div>
            <h3 className="text-lg font-bold mb-2 text-gray-900 dark:text-white">{title}</h3>
            <p className="text-gray-500 dark:text-gray-400 text-sm flex-1">{desc}</p>
            <Link href={href} className="mt-5 text-sm font-semibold text-blue-600 dark:text-blue-400 hover:underline">
              {cta} →
            </Link>
          </div>
        ))}
      </div>

      {/* ── Workflow ── */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-8">
        <h2 className="text-2xl font-bold mb-6 text-gray-900 dark:text-white">
          {t('home.how_it_works')}
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {steps.map(({ step, title, desc }) => (
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
