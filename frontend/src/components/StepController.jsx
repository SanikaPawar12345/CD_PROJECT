import { useEffect, useState } from 'react'
import axios from 'axios'
import { AnimatePresence, motion } from 'framer-motion'
import InputPanel from './InputPanel.jsx'
import TokensView from './TokensView.jsx'
import ParseTreeView from './ParseTreeView.jsx'
import MetricsView from './MetricsView.jsx'
import SuggestionView from './SuggestionView.jsx'
import ComparisonView from './ComparisonView.jsx'

const PHASE_DELAY = 1000
const TRANSITION_DELAY = 350
const API_BASE = import.meta.env.VITE_API_BASE || ''

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export default function StepController({
  onStateChange,
  history = [],
  onHistoryChange,
  compareIds = [],
  isCompareMode = false,
  onExitCompare,
  replayRequest,
}) {
  const [currentStep, setCurrentStep] = useState(0)
  const [activeTab, setActiveTab] = useState(0)
  const [data, setData] = useState(null)
  const [phaseMessage, setPhaseMessage] = useState('')
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')
  const [errorMarkers, setErrorMarkers] = useState([])
  const [hotspots, setHotspots] = useState([])
  const [selectedGrammar, setSelectedGrammar] = useState('default')
  const [grammarOptions, setGrammarOptions] = useState([
    { key: 'default', name: 'Expression Grammar v1' },
  ])
  const [grammarRules, setGrammarRules] = useState([])
  const [showGrammarRules, setShowGrammarRules] = useState(false)
  const [externalCode, setExternalCode] = useState('')
  const [externalCodeKey, setExternalCodeKey] = useState('')

  useEffect(() => {
    let active = true
    axios.get(`${API_BASE}/grammars`)
      .then((response) => {
        if (!active) return
        const grammars = Array.isArray(response.data?.grammars) ? response.data.grammars : []
        if (grammars.length > 0) {
          setGrammarOptions(grammars)
          if (!grammars.find((item) => item.key === selectedGrammar)) {
            setSelectedGrammar(grammars[0].key)
          }
        }
      })
      .catch(() => {
        // Keep default grammar list when endpoint is unavailable.
      })
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    let active = true
    axios.get(`${API_BASE}/grammar-rules`, { params: { grammar: selectedGrammar } })
      .then((response) => {
        if (!active) return
        setGrammarRules(Array.isArray(response.data?.rules) ? response.data.rules : [])
      })
      .catch(() => {
        setGrammarRules([])
      })
    return () => {
      active = false
    }
  }, [selectedGrammar])

  useEffect(() => {
    if (!replayRequest?.record) return
    replayAnalysis(replayRequest.record)
  }, [replayRequest?.key])

  const timelinePhases = ['Input', 'Tokenization', 'Parse Tree', 'Cost', 'Metrics', 'Suggestions']

  function emitState(step, payload) {
    onStateChange({ currentStep: step, data: payload })
  }

  function addToHistory(payload, sourceCode) {
    const record = {
      id: `${Date.now()}`,
      createdAt: new Date().toISOString(),
      analysis_id: payload.analysis_id,
      grammar: payload.grammar,
      source_code: sourceCode,
      parse_tree: payload.parse_tree,
      token_count: payload.token_count,
      rule_count: payload.rule_count,
      depth: payload.depth,
      node_count: payload.node_count,
      cost_score: payload.cost_score,
      analysis_payload: payload,
    }
    const next = [record, ...history].slice(0, 12)
    onHistoryChange?.(next)
  }

  async function runPhaseSequence(payload) {
    await wait(PHASE_DELAY)
    setCurrentStep(1)
    setActiveTab(0)
    emitState(1, payload)

    await wait(TRANSITION_DELAY)
    setPhaseMessage('Building Parse Tree...')
    await wait(PHASE_DELAY)
    setCurrentStep(2)
    setActiveTab(1)
    emitState(2, payload)
    setPhaseMessage('')

    await wait(TRANSITION_DELAY)
    setPhaseMessage('Computing Cost Score...')
    await wait(PHASE_DELAY)
    setCurrentStep(3)
    setActiveTab(2)
    emitState(3, payload)
    setPhaseMessage('')

    await wait(TRANSITION_DELAY)
    setPhaseMessage('Analyzing Structural Complexity...')
    await wait(PHASE_DELAY)
    setCurrentStep(4)
    setActiveTab(3)
    emitState(4, payload)
    setPhaseMessage('')

    await wait(TRANSITION_DELAY)
    setPhaseMessage('Generating Suggestions...')
    await wait(PHASE_DELAY)
    setCurrentStep(5)
    setActiveTab(4)
    emitState(5, payload)
    setPhaseMessage('')
  }

  async function replayAnalysis(record) {
    const payload = normalizeResponse(record.analysis_payload || {})
    if (!payload || !payload.tokens || payload.tokens.length === 0) {
      setError('Replay unavailable: selected history item does not contain full analysis payload.')
      return
    }

    setRunning(true)
    setError('')
    setCurrentStep(0)
    setActiveTab(0)
    setData(payload)
    setHotspots(payload.hotspots)
    setExternalCode(record.source_code || '')
    setExternalCodeKey(`${record.id}-${Date.now()}`)
    setPhaseMessage('Replaying analysis...')
    emitState(0, payload)

    try {
      await runPhaseSequence(payload)
    } finally {
      setPhaseMessage('')
      setRunning(false)
    }
  }

  function exportJson() {
    if (!data) return
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `analysis-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  function exportMarkdown() {
    if (!data) return
    const content = [
      '# Compiler Analysis Report',
      '',
      `- Grammar: ${data.grammar || 'default'}`,
      `- Token Count: ${data.token_count}`,
      `- Rule Count: ${data.rule_count}`,
      `- Max Depth: ${data.depth}`,
      `- Node Count: ${data.node_count}`,
      `- Cost Score: ${data.cost_score}`,
      '',
      '## Cost Breakdown',
      `- Token Term: ${data.cost_breakdown?.token_term ?? 0}`,
      `- Rule Term: ${data.cost_breakdown?.rule_term ?? 0}`,
      `- Depth Term: ${data.cost_breakdown?.depth_term ?? 0}`,
      `- Node Term: ${data.cost_breakdown?.node_term ?? 0}`,
      '',
      '## Tokens',
      ...data.tokens.map((tok, i) => `- ${i + 1}. ${tok.type} (${tok.value}) @ ${tok.line}:${tok.column}`),
      '',
      '## Metrics',
      `- Rule Breakdown: ${JSON.stringify(data.rule_breakdown || {}, null, 0)}`,
      '',
      '## Suggestions',
      ...data.suggestions.map((s) => `- ${s}`),
    ].join('\n')

    const blob = new Blob([content], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `analysis-${Date.now()}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  async function handleAnalyze(code, grammarKey = selectedGrammar) {
    setRunning(true)
    setError('')
    setCurrentStep(0)
    setActiveTab(0)
    setData(null)
    setErrorMarkers([])
    setHotspots([])
    emitState(0, null)

    try {
      await axios.post(`${API_BASE}/validate-syntax`, { source_code: code, grammar: grammarKey })

      setPhaseMessage('Performing Lexical Analysis...')
      const response = await axios.post(`${API_BASE}/analyze`, {
        source_code: code,
        analysis_level: 'full',
        visualization: true,
        grammar: grammarKey,
      })
      const payload = normalizeResponse(response.data)
      setData(payload)
      setHotspots(payload.hotspots)
      addToHistory(payload, code)
      await runPhaseSequence(payload)
    } catch (requestError) {
      const message =
        requestError.response?.data?.detail?.message ||
        requestError.response?.data?.detail ||
        requestError.message ||
        'Failed to analyze the program.'
      setError(message)

      const line = requestError.response?.data?.detail?.line
      const column = requestError.response?.data?.detail?.column
      if (line && column) {
        setErrorMarkers([
          {
            startLineNumber: line,
            startColumn: column,
            endLineNumber: line,
            endColumn: column + 1,
            message,
          },
        ])
      }
      setPhaseMessage('')
    } finally {
      setRunning(false)
    }
  }

  const compareRecords = history.filter((item) => compareIds.includes(item.id))
  const appliedRules = Object.entries(data?.rule_breakdown || {})
    .filter(([, count]) => Number(count) > 0)
    .sort((a, b) => Number(b[1]) - Number(a[1]))

  return (
    <div className="space-y-5">
      <InputPanel
        onAnalyze={handleAnalyze}
        disabled={running}
        markers={errorMarkers}
        hotspots={hotspots}
        grammar={selectedGrammar}
        grammarOptions={grammarOptions}
        onGrammarChange={setSelectedGrammar}
        externalCode={externalCode}
        externalCodeKey={externalCodeKey}
      />

      {!isCompareMode && (
        <section className="bg-card border border-white/10 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between gap-3">
            <h3 className="text-sm font-semibold text-secondary uppercase tracking-widest">View Grammar Rules</h3>
            <button
              type="button"
              onClick={() => setShowGrammarRules((prev) => !prev)}
              className="px-2 py-1 rounded border border-white/15 text-xs text-secondary hover:text-primary"
            >
              {showGrammarRules ? 'Hide Rules' : 'Show Rules'}
            </button>
          </div>
          {showGrammarRules && (
            <div className="mt-3 rounded-lg border border-white/10 bg-bg/50 p-3 text-sm space-y-4">
              <div>
                <p className="text-[11px] uppercase tracking-wider text-secondary mb-2">Grammar Definition Rules</p>
                <div className="space-y-1">
                  {grammarRules.length > 0 ? grammarRules.map((rule) => (
                    <p key={rule} className="font-mono text-xs text-primary">{rule}</p>
                  )) : <p className="text-secondary text-xs">No grammar rules available for this selection.</p>}
                </div>
              </div>

              <div>
                <p className="text-[11px] uppercase tracking-wider text-secondary mb-2">Rules Applied For Current Input</p>
                {data ? (
                  appliedRules.length > 0 ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {appliedRules.map(([ruleName, count]) => (
                        <div key={ruleName} className="rounded border border-white/10 bg-bg/50 px-2 py-1.5 flex items-center justify-between">
                          <span className="text-xs text-primary truncate pr-2">{ruleName}</span>
                          <span className="text-[11px] font-mono text-accent">{count}x</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-secondary text-xs">No rule applications were recorded for this run.</p>
                  )
                ) : (
                  <p className="text-secondary text-xs">Run Analyze to see which grammar rules were actually applied.</p>
                )}
              </div>
            </div>
          )}
        </section>
      )}

      {isCompareMode && (
        <ComparisonView
          records={compareRecords}
          onExit={onExitCompare}
        />
      )}

      {!isCompareMode && (
      <section className="bg-card border border-white/10 rounded-xl p-4 shadow-sm">
        <h3 className="text-sm font-semibold text-secondary uppercase tracking-widest mb-3">
          Phase Timeline
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-2">
          {timelinePhases.map((phase, idx) => {
            const selectedPhase = currentStep === 0 ? 0 : activeTab + 1
            const isCurrent = idx === selectedPhase
            const done = idx < currentStep
            const unlocked = idx <= currentStep
            return (
              <motion.button
                key={phase}
                type="button"
                onClick={() => {
                  if (!unlocked) return
                  if (idx === 0) return
                  setActiveTab(idx - 1)
                }}
                disabled={!unlocked || idx === 0}
                initial={{ opacity: 0.7 }}
                animate={{
                  opacity: isCurrent ? 1 : 0.85,
                  scale: isCurrent ? [1, 1.02, 1] : 1,
                }}
                transition={{ duration: 0.35 }}
                className={`rounded-lg border px-3 py-2 text-sm ${
                  done
                    ? 'border-green/40 bg-green/10 text-green'
                    : isCurrent
                      ? 'border-accent/50 bg-accent/15 text-accent'
                      : unlocked
                        ? 'border-white/10 bg-bg text-secondary hover:text-primary'
                        : 'border-white/10 bg-bg text-secondary/60'
                }`}
              >
                {phase}
              </motion.button>
            )
          })}
        </div>
      </section>
      )}

      {!isCompareMode && (
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
      )}

      {!isCompareMode && error && (
        <div className="bg-red/10 border border-red/40 rounded-lg p-4 text-red text-sm">
          {error}
        </div>
      )}

      {!isCompareMode && currentStep >= 1 && (
        <section className="bg-card border border-white/10 rounded-xl p-3 sm:p-4">
          <AnimatePresence mode="wait">
            {activeTab === 0 && currentStep >= 1 && (
              <motion.div
                key="tab-tokens"
                initial={{ opacity: 0, x: 14 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -14 }}
                transition={{ duration: 0.3 }}
              >
                <TokensView
                  tokens={data?.tokens || []}
                  tokenTypeCount={data?.token_type_count || {}}
                />
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
                key="tab-cost"
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
                  tokenTypeCount={data?.token_type_count || {}}
                  ruleBreakdown={data?.rule_breakdown || {}}
                  costBreakdown={data?.cost_breakdown || {}}
                  phaseTimes={data?.phase_times || {}}
                  costOnly
                />
              </motion.div>
            )}

            {activeTab === 3 && currentStep >= 4 && (
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
                  tokenTypeCount={data?.token_type_count || {}}
                  ruleBreakdown={data?.rule_breakdown || {}}
                  costBreakdown={data?.cost_breakdown || {}}
                  phaseTimes={data?.phase_times || {}}
                />
              </motion.div>
            )}

            {activeTab === 4 && currentStep >= 5 && (
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

      {!isCompareMode && data && (
        <section className="bg-card border border-white/10 rounded-xl p-4 flex gap-2 flex-wrap">
          <button
            type="button"
            onClick={exportJson}
            className="px-3 py-2 rounded-lg border border-white/15 text-sm text-secondary hover:text-primary"
          >
            Export JSON
          </button>
          <button
            type="button"
            onClick={exportMarkdown}
            className="px-3 py-2 rounded-lg border border-white/15 text-sm text-secondary hover:text-primary"
          >
            Download Report
          </button>
        </section>
      )}

    </div>
  )
}

function normalizeResponse(payload) {
  return {
    analysis_id: payload?.analysis_id || null,
    grammar: payload?.grammar || 'default',
    tokens: payload?.tokens || [],
    token_type_count: payload?.token_type_count || {},
    token_count: Number(payload?.token_count || 0),
    parse_tree: payload?.parse_tree || null,
    rule_count: Number(payload?.rule_count || 0),
    depth: Number(payload?.depth ?? payload?.max_depth ?? 0),
    node_count: Number(payload?.node_count || 0),
    rule_breakdown: payload?.rule_breakdown || {},
    cost_breakdown: payload?.cost_breakdown || {},
    cost_score: Number(payload?.cost_score || 0),
    suggestions: Array.isArray(payload?.suggestions) ? payload.suggestions : [],
    hotspots: Array.isArray(payload?.hotspots) ? payload.hotspots : [],
    phase_times: payload?.phase_times || {},
  }
}
