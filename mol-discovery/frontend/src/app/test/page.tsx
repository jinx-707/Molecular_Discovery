'use client'

export default function TestPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 p-10">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-8 mb-6">
          <h1 className="text-4xl font-bold text-blue-600 dark:text-blue-400 mb-4">
            🎨 Tailwind CSS Test Page
          </h1>
          <p className="text-gray-700 dark:text-gray-300 text-lg mb-6">
            If you can see styled content with colors, gradients, and proper spacing, Tailwind is working perfectly!
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-red-100 dark:bg-red-900 p-4 rounded-lg">
              <h3 className="font-bold text-red-800 dark:text-red-200">Red Card</h3>
              <p className="text-red-600 dark:text-red-300">This is red</p>
            </div>
            <div className="bg-green-100 dark:bg-green-900 p-4 rounded-lg">
              <h3 className="font-bold text-green-800 dark:text-green-200">Green Card</h3>
              <p className="text-green-600 dark:text-green-300">This is green</p>
            </div>
            <div className="bg-blue-100 dark:bg-blue-900 p-4 rounded-lg">
              <h3 className="font-bold text-blue-800 dark:text-blue-200">Blue Card</h3>
              <p className="text-blue-600 dark:text-blue-300">This is blue</p>
            </div>
          </div>

          <div className="space-y-4">
            <button className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-3 px-6 rounded-lg shadow-lg transition-all duration-200 transform hover:scale-105">
              Hover Me!
            </button>
            
            <div className="flex gap-2">
              <span className="px-3 py-1 bg-purple-500 text-white rounded-full text-sm">Badge 1</span>
              <span className="px-3 py-1 bg-pink-500 text-white rounded-full text-sm">Badge 2</span>
              <span className="px-3 py-1 bg-indigo-500 text-white rounded-full text-sm">Badge 3</span>
            </div>
          </div>
        </div>

        <div className="bg-yellow-100 dark:bg-yellow-900 border-l-4 border-yellow-500 p-4 rounded">
          <p className="text-yellow-800 dark:text-yellow-200 font-semibold">
            ✅ If you see this styled correctly, Tailwind CSS is working!
          </p>
        </div>
      </div>
    </div>
  )
}
