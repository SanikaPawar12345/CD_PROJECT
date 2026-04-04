import { useState } from 'react'
import axios from 'axios'
import { AnimatePresence, motion } from 'framer-motion'
import InputPanel from './InputPanel.jsx'
import TokenView from './TokenView.jsx'
import ParseTreeView from './ParseTreeView.jsx'
import MetricsView from './MetricsView.jsx'
import SuggestionView from './SuggestionView.jsx'

const PHASE_DELAY = 1000
const TRANSITION_DELAY = 350

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export default function StepController({ onStateChange }) {
  const [currentStep, setCurrentStep] = useState(0)
  const [activeTab, setActiveTab] = useState(0)
  const [data, setData] = useState(null)
  const [phaseMessage, setPhaseMessage] = useState('')
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')

  const tabs = [
    { label: 'Step 1: Tokens', step: 1 },
    { label: 'Step 2: Parse Tree', step: 2 },
    { label: 'Step 3: Metrics', step: 3 },
    { label: 'Step 4: Suggestions', step: 4 },
  ]

  function emitState(step, payload) {
    onStateChange({ currentStep: step, data: payload })
  }

  async function handleAnalyze(code) {
    setRunning(true)
    setError('')
    setCurrentStep(0)
    setActiveTab(0)
    setData(null)
    emitState(0, null)

    try {
      setPhaseMessage('Performing Lexical Analysis...')
      const response = await axios.post('/analyze', {
        code,
        source_code: code,
      })
      const payload = normalizeResponse(response.data)
      setData(payload)

      await wait(PHASE_DELAY)
      setCurrentStep(1)
      setActiveTab(0)
      emitState(1, payload)
      setPhaseMessage('')

      await wait(TRANSITION_DELAY)
      setPhaseMessage('Building Parse Tree...')
      await wait(PHASE_DELAY)
      setCurrentStep(2)
      setActiveTab(1)
      emitState(2, payload)
      setPhaseMessage('')

      await wait(TRANSITION_DELAY)
      setPhaseMessage('Analyzing Structural Complexity...')
      await wait(PHASE_DELAY)
      setCurrentStep(3)
      setActiveTab(2)
      emitState(3, payload)
      setPhaseMessage('')

      await wait(TRANSITION_DELAY)
      setPhaseMessage('Generating Suggestions...')
      await wait(PHASE_DELAY)
      setCurrentStep(4)
      setActiveTab(3)
      emitState(4, payload)
      setPhaseMessage('')
    } catch (requestError) {
      const message =
        requestError.response?.data?.detail ||
        requestError.message ||
        'Failed to analyze the program.'
      setError(message)
      setPhaseMessage('')
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="space-y-5">
      <InputPanel onAnalyze={handleAnalyze} disabled={running} />

      <AnimatePresence>
        {phaseMessage && (
          <motion.div
            key={phaseMessage}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="bg-card border border-accent/40 rounded-lg p-4 flex items-center gap-3"
          >
            <span className="w-2.5 h-2.5 rounded-full bg-cyan animate-pulse" />
            <span className="text-sm text-primary">{phaseMessage}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {error && (
        <div className="bg-red/10 border border-red/40 rounded-lg p-4 text-red text-sm">
          {error}
        </div>
      )}

      {currentStep >= 1 && (
        <section className="bg-card border border-white/10 rounded-xl p-3 sm:p-4">
          <div className="flex flex-wrap gap-2 mb-4">
            {tabs.map((tab, index) => {
              const unlocked = currentStep >= tab.step
              const selected = activeTab === index

              return (
                <button
                  key={tab.label}
                  type="button"
                  onClick={() => unlocked && setActiveTab(index)}
                  disabled={!unlocked}
                  className={`px-3 py-2 rounded-lg text-sm transition ${
                    selected
                      ? 'bg-accent text-white'
                      : unlocked
                        ? 'bg-bg text-secondary hover:text-primary border border-white/10'
                        : 'bg-bg/50 text-secondary/50 border border-white/10 cursor-not-allowed'
                  }`}
                >
                  {tab.label}
                </button>
              )
            })}
          </div>

          <AnimatePresence mode="wait">
            {activeTab === 0 && currentStep >= 1 && (
              <motion.div
                key="tab-tokens"
                initial={{ opacity: 0, x: 14 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -14 }}
                transition={{ duration: 0.3 }}
              >
                <TokenView tokens={data?.tokens || []} />
              </motion.div>
            )}

            {activeTab === 1 && currentStep >= 2 && (
              <motion.div
                key="tab-tree"
                initial={{ opacity: 0, x: 14 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -14 }}
                transition={{ duration: 0.3 }}
              >
                <ParseTreeView parseTree={data?.parse_tree} />
              </motion.div>
            )}

            {activeTab === 2 && currentStep >= 3 && (
              <motion.div
                key="tab-metrics"
                initial={{ opacity: 0, x: 14 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -14 }}
                transition={{ duration: 0.3 }}
              >
                <MetricsView
                  tokenCount={data?.token_count || 0}
                  ruleCount={data?.rule_count || 0}
                  depth={data?.depth || 0}
                  costScore={data?.cost_score || 0}
                />
              </motion.div>
            )}

            {activeTab === 3 && currentStep >= 4 && (
              <motion.div
                key="tab-suggestions"
                initial={{ opacity: 0, x: 14 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -14 }}
                transition={{ duration: 0.3 }}
              >
                <SuggestionView suggestions={data?.suggestions || []} />
              </motion.div>
            )}
          </AnimatePresence>
        </section>
      )}
    </div>
  )
}

function normalizeResponse(payload) {
  return {
    tokens: payload?.tokens || [],
    token_count: Number(payload?.token_count || 0),
    parse_tree: payload?.parse_tree || null,
    rule_count: Number(payload?.rule_count || 0),
    depth: Number(payload?.depth ?? payload?.max_depth ?? 0),
    node_count: Number(payload?.node_count || 0),
    cost_score: Number(payload?.cost_score || 0),
    suggestions: Array.isArray(payload?.suggestions) ? payload.suggestions : [],
  }
}
