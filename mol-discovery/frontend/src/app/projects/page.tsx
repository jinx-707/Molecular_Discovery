'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { project } from '@/services/api'

export default function ProjectView() {
  const [projects, setProjects] = useState<any[]>([])
  const [newProjectName, setNewProjectName] = useState('')
  const [selectedProject, setSelectedProject] = useState<any>(null)
  const [feed, setFeed] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setError('')
      setLoading(true)
      const response = await project.create(newProjectName)
      setProjects([...projects, response.data])
      setNewProjectName('')
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to create project')
    } finally {
      setLoading(false)
    }
  }

  const handleSelectProject = async (proj: any) => {
    try {
      setSelectedProject(proj)
      setError('')
      const response = await project.feed(proj.id)
      setFeed(response.data)
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load project feed')
    }
  }

  return (
    <div className="container mx-auto py-12 px-4">
      <h1 className="text-4xl font-bold mb-8">Projects</h1>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-6">
            <h2 className="text-2xl font-bold mb-4">Create New Project</h2>
            <form onSubmit={handleCreateProject} className="space-y-4">
              <input
                type="text"
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                placeholder="Project name"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                required
              />
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Creating...' : 'Create Project'}
              </Button>
            </form>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-bold mb-4">Your Projects</h2>
            {projects.length === 0 ? (
              <p className="text-gray-500">No projects yet. Create one to get started!</p>
            ) : (
              <div className="space-y-2">
                {projects.map((proj) => (
                  <div
                    key={proj.id}
                    className={`p-3 rounded-lg cursor-pointer transition-colors ${
                      selectedProject?.id === proj.id
                        ? 'bg-blue-100 dark:bg-blue-900'
                        : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                    onClick={() => handleSelectProject(proj)}
                  >
                    <p className="font-semibold">{proj.name}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {new Date(proj.created_at).toLocaleDateString()}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="lg:col-span-2">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-bold mb-4">
              {selectedProject ? selectedProject.name : 'Select a project'}
            </h2>
            
            {!selectedProject ? (
              <p className="text-gray-500">Select a project from the list to view its activity feed</p>
            ) : feed.length === 0 ? (
              <p className="text-gray-500">No activity yet in this project</p>
            ) : (
              <div className="space-y-4">
                {feed.map((item, idx) => (
                  <div key={idx} className="border-l-4 border-blue-500 pl-4 py-2">
                    <p className="font-semibold">{item.type}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{item.description}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(item.timestamp).toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
