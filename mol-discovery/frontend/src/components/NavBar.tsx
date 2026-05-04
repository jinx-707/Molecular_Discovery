'use client'
import Link from 'next/link'
import LanguageToggle from './LanguageToggle'
import { useT } from '@/lib/i18n'
import { useAutoTranslate } from '@/hooks/useAutoTranslate'

export default function NavBar() {
  const t = useT()
  useAutoTranslate() // re-translates DOM on every route change when locale === 'kn'

  const links = [
    { href: '/',            label: t('nav.dashboard')   },
    { href: '/discovery',   label: t('nav.discovery')   },
    { href: '/experiments', label: t('nav.experiments') },
    { href: '/models',      label: t('nav.models')      },
    { href: '/projects',    label: t('nav.projects')    },
    { href: '/enzyme',      label: t('nav.enzyme')      },
    { href: '/pathways',    label: t('nav.pathways')    },
  ]

  return (
    <nav className="bg-white dark:bg-gray-800 shadow-lg">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link href="/">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white cursor-pointer">
                {t('nav.brand')}
              </h1>
            </Link>
          </div>
          <div className="flex space-x-1 items-center">
            {links.map(({ href, label }) => (
              <Link
                key={href}
                href={href}
                className="px-3 py-2 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300
                           hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                {label}
              </Link>
            ))}
            <div className="ml-3">
              <LanguageToggle />
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}
