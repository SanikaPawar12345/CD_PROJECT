import { useState } from 'react'
import Sidebar from './components/Sidebar.jsx'
import StepController from './components/StepController.jsx'

export default function App() {
  const [summary, setSummary] = useState({ currentStep: 0, data: null })

  return (
    <div className="min-h-screen bg-bg text-primary">
      <header className="border-b border-white/10 px-6 py-4">
        <h1 className="text-lg font-semibold">Phase-Wise Compiler Cost Analyzer</h1>
        <p className="text-secondary text-sm mt-1">Interactive step-by-step compiler dashboard</p>
      </header>

      <div className="flex flex-col lg:flex-row min-h-[calc(100vh-73px)]">
        <Sidebar currentStep={summary.currentStep} data={summary.data} />
        <main className="flex-1 p-4 sm:p-6 overflow-y-auto">
          <StepController onStateChange={setSummary} />
        </main>
      </div>
    </div>
  )
}
