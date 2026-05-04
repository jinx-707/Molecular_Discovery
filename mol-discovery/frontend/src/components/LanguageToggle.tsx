'use client'
import { useState } from 'react'
import { useI18nStore } from '@/lib/i18n'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

/**
 * Language toggle that does two things when switching to Kannada:
 *  1. Instantly swaps all static strings via the Zustand i18n store (JSON-based).
 *  2. Walks the DOM for any remaining English text nodes and batch-translates
 *     them via POST /api/translate/page-batch (Sarvam API with separator trick).
 *
 * Switching back to English reloads the page — cleanest way to restore
 * original DOM text without tracking every mutation.
 */
export default function LanguageToggle() {
  const { locale, setLocale } = useI18nStore()
  const [translating, setTranslating] = useState(false)
  const isKn = locale === 'kn'

  const handleClick = async () => {
    if (isKn) {
      // Restore English — reload is the simplest reliable reset
      setLocale('en')
      window.location.reload()
      return
    }

    // ── Step 1: instant static swap ──────────────────────────────────
    setLocale('kn')
    setTranslating(true)

    // Give React one tick to re-render with Kannada static strings
    await new Promise(r => setTimeout(r, 80))

    // ── Step 2: collect remaining English text nodes ─────────────────
    const nodes: Text[] = []
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode(node) {
          const el = node.parentElement
          if (!el) return NodeFilter.FILTER_REJECT
          // Skip invisible / non-content elements
          if (el.closest('script, style, noscript, [data-no-translate]'))
            return NodeFilter.FILTER_REJECT
          // Skip already-translated nodes
          if (el.closest('[data-translated="true"]'))
            return NodeFilter.FILTER_REJECT
          const text = node.textContent?.trim() ?? ''
          // Only nodes that still contain Latin characters
          if (text.length > 1 && /[a-zA-Z]{2,}/.test(text))
            return NodeFilter.FILTER_ACCEPT
          return NodeFilter.FILTER_REJECT
        },
      }
    )

    let node: Node | null
    while ((node = walker.nextNode())) nodes.push(node as Text)

    if (nodes.length === 0) {
      setTranslating(false)
      return
    }

    const originalTexts = nodes.map(n => n.textContent?.trim() ?? '')

    // ── Step 3: batch-translate via backend ──────────────────────────
    try {
      const res = await fetch(`${API_BASE}/api/translate/page-batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texts: originalTexts, source: 'en-IN', target: 'kn-IN' }),
      })

      if (res.ok) {
        const { translations }: { translations: string[] } = await res.json()
        nodes.forEach((n, i) => {
          if (translations[i] && translations[i] !== n.textContent) {
            n.textContent = translations[i]
            // Mark parent so we don't re-translate on future passes
            if (n.parentElement)
              n.parentElement.setAttribute('data-translated', 'true')
          }
        })
      }
    } catch (err) {
      // Non-fatal — static strings are already in Kannada
      console.warn('Page-batch translation failed (static strings still translated):', err)
    }

    setTranslating(false)
  }

  return (
    <button
      onClick={handleClick}
      disabled={translating}
      title={isKn ? 'Switch to English' : 'ಕನ್ನಡಕ್ಕೆ ಬದಲಿಸಿ'}
      className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border
                 border-blue-400 dark:border-blue-500
                 bg-blue-50 dark:bg-blue-900/30
                 text-blue-700 dark:text-blue-300
                 text-sm font-semibold
                 hover:bg-blue-100 dark:hover:bg-blue-800/40
                 disabled:opacity-60 disabled:cursor-wait
                 transition-colors select-none"
    >
      <span className="text-base leading-none">
        {translating ? '⏳' : isKn ? '🇮🇳' : '🌐'}
      </span>
      <span>
        {translating ? 'ಅನುವಾದಿಸಲಾಗುತ್ತಿದೆ…' : isKn ? 'English' : 'ಕನ್ನಡ'}
      </span>
    </button>
  )
}
