import React from 'react'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import Link from 'next/link'
import './globals.css'
import { ThemeProvider } from '@/components/theme-provider'
import NavBar from '@/components/NavBar'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'MolDiscovery - AI Platform for Catalyst & Enzyme Discovery',
  description: 'AI-powered catalyst and enzyme discovery platform for GPS Renewables',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
          <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-gray-900 dark:to-gray-800">
            <NavBar />
            <main>{children}</main>
          </div>
        </ThemeProvider>
      </body>
    </html>
  )
}
