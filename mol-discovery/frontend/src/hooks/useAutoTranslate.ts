'use client'
/**
 * useAutoTranslate
 * ----------------
 * Re-runs the DOM translation pass whenever the pathname changes
 * (i.e. the user navigates to a new page) AND the locale is 'kn'.
 *
 * Works with Next.js App Router — uses usePathname() instead of the
 * Pages-Router-only router.events API.
 *
 * Strategy (same as LanguageToggle):
 *  1. Walk text nodes that still contain Latin characters.
 *  2. POST to /api/translate/page-batch (glossary + Sarvam, one call per chunk).
 *  3. Write translations back in-place; mark parents data-translated="true".
 *
 * A small delay (120 ms) lets React finish painting the new page before
 * the walker runs, so it sees the fully-rendered content.
 */
import { useEffect, useRef } from 'react'
import { usePathname } from 'next/navigation'
import { useI18nStore } from '@/lib/i18n'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const LATIN = /[a-zA-Z]{2,}/

async function translateDom() {
  // Collect text nodes that still have Latin content
  const nodes: Text[] = []
  const walker = document.createTreeWalker(
    document.body,
    NodeFilter.SHOW_TEXT,
    {
      acceptNode(node) {
        const el = node.parentElement
        if (!el) return NodeFilter.FILTER_REJECT
        if (el.closest('script, style, noscript, [data-no-translate], [data-translated="true"]'))
          return NodeFilter.FILTER_REJECT
        const text = node.textContent?.trim() ?? ''
        return text.length > 1 && LATIN.test(text)
          ? NodeFilter.FILTER_ACCEPT
          : NodeFilter.FILTER_REJECT
      },
    }
  )

  let n: Node | null
  while ((n = walker.nextNode())) nodes.push(n as Text)
  if (nodes.length === 0) return

  const texts = nodes.map(n => n.textContent?.trim() ?? '')

  try {
    const res = await fetch(`${API_BASE}/api/translate/page-batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ texts, source: 'en-IN', target: 'kn-IN' }),
    })
    if (!res.ok) return

    const { translations }: { translations: string[] } = await res.json()
    nodes.forEach((node, i) => {
      if (translations[i] && translations[i] !== node.textContent) {
        node.textContent = translations[i]
        node.parentElement?.setAttribute('data-translated', 'true')
      }
    })
  } catch {
    // Non-fatal — static strings from the JSON files are already in Kannada
  }
}

export function useAutoTranslate() {
  const locale = useI18nStore(s => s.locale)
  const pathname = usePathname()
  // Track in-flight requests so we don't stack them
  const inFlight = useRef(false)

  useEffect(() => {
    if (locale !== 'kn') return
    if (inFlight.current) return

    inFlight.current = true
    // Small delay — let React finish painting the new route
    const id = setTimeout(async () => {
      await translateDom()
      inFlight.current = false
    }, 120)

    return () => {
      clearTimeout(id)
      inFlight.current = false
    }
  }, [locale, pathname]) // re-runs on every navigation while in Kannada mode
}
