import { useEffect, useState } from 'react'
import axios from 'axios'
import Sidebar from './components/Sidebar.jsx'
import StepController from './components/StepController.jsx'

const API_BASE = import.meta.env.VITE_API_BASE || ''

export default function App() {
  function ensureUniqueIds(items) {
    const seen = new Set()
    return items.map((item, index) => {
      let nextId = item.id || `${item.analysis_id || 'analysis'}-${index}`
      while (seen.has(nextId)) {
        nextId = `${nextId}-${Math.random().toString(16).slice(2)}`
      }
      seen.add(nextId)
      return nextId === item.id ? item : { ...item, id: nextId }
    })
  }

  const [summary, setSummary] = useState({ currentStep: 0, data: null })
  const [theme, setTheme] = useState('dark')
  const [isCompareMode, setIsCompareMode] = useState(false)
  const [replayRequest, setReplayRequest] = useState(null)
  const [history, setHistory] = useState(() => {
    try {
      const raw = localStorage.getItem('analysis_history')
      const parsed = raw ? JSON.parse(raw) : []
      return ensureUniqueIds(parsed)
    } catch {
      return []
    }
  })
  const [compareIds, setCompareIds] = useState([])
  const [usageStats, setUsageStats] = useState(null)

  function toggleCompareSelection(id) {
    setCompareIds((prev) => {
      if (prev.includes(id)) {
        return prev.filter((item) => item !== id)
      }
      return [...prev, id]
    })
  }

  function handleExitComparison() {
    setIsCompareMode(false)
    setCompareIds([])
  }

  function handleReplay(record) {
    setIsCompareMode(false)
    setCompareIds([])
    setReplayRequest({
      key: `${record.id}-${Date.now()}`,
      record,
    })
  }

  function handleStartComparison() {
    if (compareIds.length >= 2) {
      setIsCompareMode(true)
    }
  }

  useEffect(() => {
    if (compareIds.length >= 2) {
      setIsCompareMode(true)
    }
    if (compareIds.length < 2) {
      setIsCompareMode(false)
    }
  }, [compareIds])

  useEffect(() => {
    document.body.classList.toggle('theme-light', theme === 'light')
  }, [theme])

  useEffect(() => {
    let active = true

    async function hydrateFromBackend() {
      try {
        const [historyResponse, statsResponse] = await Promise.all([
          axios.get(`${API_BASE}/history?limit=40`),
          axios.get(`${API_BASE}/stats`),
        ])

        if (!active) return

        const backendItems = Array.isArray(historyResponse.data?.items) ? historyResponse.data.items : []
        if (backendItems.length > 0) {
          const mapped = backendItems.map((item) => ({
            id: item.analysis_id || item.source_hash || `${item.timestamp}-${Math.random()}`,
            createdAt: item.timestamp || new Date().toISOString(),
            analysis_id: item.analysis_id || null,
            grammar: item.grammar || 'default',
            source_code: item.source_code || '',
            token_count: Number(item.analysis_payload?.token_count ?? item.token_count ?? 0),
            rule_count: Number(item.analysis_payload?.rule_count ?? item.rule_count ?? 0),
            depth: Number(item.analysis_payload?.max_depth ?? item.depth ?? 0),
            node_count: Number(item.analysis_payload?.node_count ?? item.node_count ?? 0),
            cost_score: Number(item.analysis_payload?.cost_score ?? item.cost_score ?? 0),
            peak_memory_kb: Number(item.analysis_payload?.peak_memory_kb ?? item.peak_memory_kb ?? 0),
            ai_processing_ms: Number(item.analysis_payload?.ai_processing_ms ?? item.ai_processing_ms ?? 0),
            semantic_analysis: item.analysis_payload?.semantic_analysis ?? item.semantic_analysis ?? null,
            analysis_payload: item.analysis_payload || null,
          }))
          const deduped = ensureUniqueIds(mapped)
          setHistory(deduped)
          localStorage.setItem('analysis_history', JSON.stringify(deduped))
        }

        setUsageStats(statsResponse.data || null)
      } catch {
        // Local storage history remains the fallback when backend sync is unavailable.
      }
    }

    hydrateFromBackend()
    return () => {
      active = false
    }
  }, [])

  return (
    <div className="min-h-screen bg-bg text-primary">
      <header className="border-b border-white/10 px-6 py-4 flex items-start justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold">Phase-Wise Compiler Cost Analyzer</h1>
          <p className="text-secondary text-sm mt-1">Interactive step-by-step compiler dashboard</p>
        </div>
        <button
          type="button"
          onClick={() => setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))}
          className="px-3 py-2 rounded-lg border border-white/15 text-sm text-secondary hover:text-primary"
        >
          {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
        </button>
      </header>

      <div className="flex flex-col lg:flex-row h-[calc(100vh-73px)] overflow-hidden">
        <Sidebar
          currentStep={summary.currentStep}
          data={summary.data}
          history={history}
          compareIds={compareIds}
          onToggleCompare={toggleCompareSelection}
          onStartCompare={handleStartComparison}
          isCompareMode={isCompareMode}
          usageStats={usageStats}
          onReplay={handleReplay}
        />
        <main className="flex-1 p-4 sm:p-6 overflow-y-auto h-full">
          <StepController
            onStateChange={setSummary}
            history={history}
            onHistoryChange={(next) => {
              setHistory(next)
              localStorage.setItem('analysis_history', JSON.stringify(next))
            }}
            compareIds={compareIds}
            isCompareMode={isCompareMode}
            onExitCompare={handleExitComparison}
            replayRequest={replayRequest}
          />
        </main>
      </div>
    </div>
  )
}
