import { useState } from 'react'
import axios from 'axios'
import { AnimatePresence, motion } from 'framer-motion'
import InputSection  from './components/InputSection.jsx'
import Sidebar       from './components/Sidebar.jsx'
import TokensView    from './components/TokensView.jsx'
import ParseTreeView from './components/ParseTreeView.jsx'
import MetricsView   from './components/MetricsView.jsx'
import SuggestionCard from './components/SuggestionCard.jsx'

const STEPS = ['Tokens', 'Parse Tree', 'Metrics']

export default function App() {
  const [result,    setResult]    = useState(null)
  const [loading,   setLoading]   = useState(false)
  const [phase,     setPhase]     = useState('')   // animation status text
  const [activeTab, setActiveTab] = useState(0)
  const [error,     setError]     = useState('')

  async function handleAnalyze(source) {
    setError('')
    setResult(null)
    setActiveTab(0)
    setLoading(true)

    try {
      setPhase('Tokenizing…')
      await delay(600)
      setPhase('Building Parse Tree…')
      await delay(500)
      setPhase('Computing Metrics…')

      const { data } = await axios.post('http://localhost:8000/analyze', {
        source_code: source,
      })

      await delay(400)
      setResult(data)
      setPhase('')
    } catch (err) {
      const msg =
        err.response?.data?.detail || err.message || 'Unknown error'
      setError(msg)
      setPhase('')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-bg text-primary flex flex-col">
      {/* ── Header ── */}
      <header className="border-b border-white/10 px-6 py-4 flex items-center gap-3">
        <span className="text-accent text-2xl font-bold font-mono">{'</>'}</span>
        <div>
          <h1 className="text-lg font-semibold leading-none">
            Phase-Wise Compiler Cost Analyzer
          </h1>
          <p className="text-secondary text-xs mt-0.5">
            Lexical · Syntax · Metrics · Cost · Advice
          </p>
        </div>
      </header>

      {/* ── Body ── */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left panel */}
        <main className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
          {/* Input */}
          <InputSection onAnalyze={handleAnalyze} loading={loading} />

          {/* Phase animation overlay */}
          <AnimatePresence>
            {loading && (
              <motion.div
                key="phase-banner"
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                className="bg-card border border-accent/30 rounded-xl p-4 flex items-center gap-3"
              >
                <span className="inline-block w-3 h-3 rounded-full bg-accent animate-pulse" />
                <span className="text-accent font-mono text-sm">{phase}</span>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Error */}
          {error && (
            <div className="bg-danger/10 border border-danger/40 rounded-xl p-4 text-danger text-sm font-mono">
              ⚠ {error}
            </div>
          )}

          {/* Results tabs */}
          <AnimatePresence>
            {result && (
              <motion.div
                key="results"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
                className="flex flex-col gap-6"
              >
                {/* Suggestion at top */}
                <SuggestionCard suggestions={result.suggestions} />

                {/* Tab bar */}
                <div className="flex gap-2">
                  {STEPS.map((s, i) => (
                    <button
                      key={s}
                      onClick={() => setActiveTab(i)}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                        activeTab === i
                          ? 'bg-accent text-white shadow-lg shadow-accent/20'
                          : 'bg-card text-secondary hover:text-primary hover:bg-white/5'
                      }`}
                    >
                      Step {i + 1}: {s}
                    </button>
                  ))}
                </div>

                {/* Tab content */}
                <AnimatePresence mode="wait">
                  {activeTab === 0 && (
                    <motion.div key="tok"
                      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                      <TokensView
                        tokens={result.tokens}
                        tokenTypeCount={result.token_type_count}
                      />
                    </motion.div>
                  )}
                  {activeTab === 1 && (
                    <motion.div key="tree"
                      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                      <ParseTreeView tree={result.parse_tree} />
                    </motion.div>
                  )}
                  {activeTab === 2 && (
                    <motion.div key="metrics"
                      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                      <MetricsView
                        metrics={result.metrics}
                        costBreakdown={result.cost_breakdown}
                        costScore={result.cost_score}
                      />
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            )}
          </AnimatePresence>
        </main>

        {/* Right sidebar */}
        <Sidebar result={result} />
      </div>
    </div>
  )
}

function delay(ms) {
  return new Promise(res => setTimeout(res, ms))
}
