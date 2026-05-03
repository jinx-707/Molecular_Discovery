'use client'

import React, { useState } from 'react'
import Link from 'next/link'

interface Project {
  id: string
  name: string
  reaction: string
  created_at: string
  run_count: number
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [name, setName]         = useState('')
  const [reaction, setReaction] = useState('')

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return
    const proj: Project = {
      id:         crypto.randomUUID(),
      name:       name.trim(),
      reaction:   reaction.trim(),
      created_at: new Date().toISOString(),
      run_count:  0,
    }
    setProjects(p => [proj, ...p])
    setName('')
    setReaction('')
  }

  return (
    <div className="max-w-5xl mx-auto py-10 px-4 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Projects</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Organise discovery campaigns by project.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Create form */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6">
          <h2 className="text-lg font-bold mb-4 text-gray-900 dark:text-white">New Project</h2>
          <form onSubmit={handleCreate} className="space-y-3">
            <div>
              <label className="block text-sm font-semibold mb-1 text-gray-700 dark:text-gray-300">
                Project Name
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Ethanol-to-Jet Q3"
                className="w-full p-2.5 border border-gray-300 dark:border-gray-600 rounded-lg
                           bg-white dark:bg-gray-700 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                value={name}
                onChange={e => setName(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-semibold mb-1 text-gray-700 dark:text-gray-300">
                Target Reaction (optional)
              </label>
              <input
                type="text"
                placeholder="e.g. ethanol to jet fuel"
                className="w-full p-2.5 border border-gray-300 dark:border-gray-600 rounded-lg
                           bg-white dark:bg-gray-700 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                value={reaction}
                onChange={e => setReaction(e.target.value)}
              />
            </div>
            <button
              type="submit"
              className="w-full py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white
                         font-semibold text-sm transition-colors"
            >
              Create Project
            </button>
          </form>
        </div>

        {/* Project list */}
        <div className="lg:col-span-2 space-y-3">
          {projects.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-10 text-center text-gray-400">
              <div className="text-4xl mb-3">📁</div>
              <p>No projects yet. Create one to organise your discovery runs.</p>
              <Link
                href="/discovery"
                className="mt-4 inline-block text-sm text-blue-600 dark:text-blue-400 hover:underline"
              >
                Or start a discovery run directly →
              </Link>
            </div>
          ) : (
            projects.map(proj => (
              <div
                key={proj.id}
                className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-5
                           flex items-center justify-between gap-4"
              >
                <div>
                  <div className="font-semibold text-gray-900 dark:text-white">{proj.name}</div>
                  {proj.reaction && (
                    <div className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                      {proj.reaction}
                    </div>
                  )}
                  <div className="text-xs text-gray-400 mt-1">
                    Created {new Date(proj.created_at).toLocaleDateString()}
                  </div>
                </div>
                <Link
                  href={`/discovery?reaction=${encodeURIComponent(proj.reaction || '')}`}
                  className="flex-shrink-0 px-4 py-2 rounded-lg bg-blue-50 dark:bg-blue-900/30
                             text-blue-700 dark:text-blue-300 text-sm font-semibold hover:bg-blue-100
                             dark:hover:bg-blue-900/50 transition-colors"
                >
                  Run Discovery
                </Link>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
