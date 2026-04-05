import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || ''

function programLabel(index) {
  return `Program ${String.fromCharCode(65 + index)}`
}

function deltaLabel(current, baseline) {
  if (baseline === null || baseline === undefined) return null
  const delta = Number(current || 0) - Number(baseline || 0)
  const sign = delta > 0 ? '+' : ''
  const arrow = delta > 0 ? '↑' : delta < 0 ? '↓' : '→'
  const tone = delta === 0 ? 'text-secondary' : delta > 0 ? 'text-red' : 'text-green'
  return <span className={`text-[11px] ml-1 ${tone}`}>({sign}{delta} {arrow})</span>
}

export default function ComparisonView({ records = [], onExit }) {
  const [diffs, setDiffs] = useState([])
  const [diffError, setDiffError] = useState('')
  const baseline = records[0]

  useEffect(() => {
    let cancelled = false

    async function runDiffs() {
      setDiffError('')
      if (records.length < 2) {
        setDiffs([])
        return
      }

      const comparable = records.slice(1).filter((record) => baseline.source_code && record.source_code)

      try {
        const responses = await Promise.all(comparable.map((record) => axios.post(`${API_BASE}/parse-tree-diff`, {
          source_a: baseline.source_code,
          source_b: record.source_code,
          grammar: baseline.grammar || 'default',
          visualization: false,
        })))

        if (cancelled) return
        setDiffs(responses.map((response, index) => ({
          targetId: comparable[index].id,
          targetLabel: programLabel(index + 1),
          summary: response.data?.summary || {},
          samples: response.data?.samples || {},
        })))
      } catch {
        if (cancelled) return
        setDiffError('Parse-tree diff is unavailable for one or more selected programs.')
      }
    }

    runDiffs()
    return () => {
      cancelled = true
    }
  }, [records])

  return (
    <motion.section
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="bg-card border border-white/10 rounded-xl p-5 shadow-sm"
    >
      <div className="flex flex-wrap items-start justify-between gap-3 mb-5">
        <div>
          <h2 className="text-lg font-semibold text-primary">Comparison Mode Active</h2>
          <p className="text-sm text-secondary mt-1">
            Selected analyses are shown side-by-side for quick metric comparisons.
          </p>
        </div>
        <button
          type="button"
          onClick={onExit}
          className="px-3 py-2 rounded-lg border border-accent/40 text-sm text-accent hover:bg-accent hover:text-white transition"
        >
          Exit Comparison
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
        {records.map((record, index) => (
          <article
            key={record.id}
            className="rounded-xl border border-white/10 bg-bg/50 p-4 shadow-sm"
          >
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-primary">{programLabel(index)}</h3>
              <span className="text-[11px] text-secondary font-mono">
                {new Date(record.createdAt).toLocaleTimeString()}
              </span>
            </div>

            <div className="space-y-2 text-sm">
              <p className="text-secondary">Tokens: <span className="text-primary font-semibold">{record.token_count}</span>{index > 0 && deltaLabel(record.token_count, baseline?.token_count)}</p>
              <p className="text-secondary">Rules: <span className="text-primary font-semibold">{record.rule_count}</span>{index > 0 && deltaLabel(record.rule_count, baseline?.rule_count)}</p>
              <p className="text-secondary">Depth: <span className="text-primary font-semibold">{record.depth}</span>{index > 0 && deltaLabel(record.depth, baseline?.depth)}</p>
              <p className="text-secondary">Nodes: <span className="text-primary font-semibold">{record.node_count}</span>{index > 0 && deltaLabel(record.node_count, baseline?.node_count)}</p>
              <p className="text-secondary">Cost: <span className="text-primary font-semibold">{record.cost_score}</span>{index > 0 && deltaLabel(record.cost_score, baseline?.cost_score)}</p>
            </div>
          </article>
        ))}
      </div>

      {records.length >= 2 && (
        <div className="mt-6 rounded-xl border border-white/10 p-4 bg-bg/50">
          <h3 className="text-sm font-semibold text-primary mb-3">Parse-Tree Diff Mode</h3>
          <p className="text-xs text-secondary mb-4">
            Baseline: Program A. Diffs are computed against each other selected program.
          </p>

          {diffError && (
            <div className="text-xs border border-red/40 bg-red/10 text-red rounded px-3 py-2 mb-3">
              {diffError}
            </div>
          )}

          <div className="space-y-3">
            {diffs.map((diff) => (
              <div key={diff.targetId} className="rounded-lg border border-white/10 bg-card p-3">
                <p className="text-xs font-semibold text-secondary mb-2">Program A vs {diff.targetLabel}</p>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-xs">
                  <span className="rounded border border-white/10 px-2 py-1">Added: <b>{diff.summary.added || 0}</b></span>
                  <span className="rounded border border-white/10 px-2 py-1">Removed: <b>{diff.summary.removed || 0}</b></span>
                  <span className="rounded border border-white/10 px-2 py-1">Changed: <b>{diff.summary.changed || 0}</b></span>
                  <span className="rounded border border-white/10 px-2 py-1">Nodes A: <b>{diff.summary.total_a || 0}</b></span>
                  <span className="rounded border border-white/10 px-2 py-1">Nodes B: <b>{diff.summary.total_b || 0}</b></span>
                </div>
                {(diff.samples?.changed || []).length > 0 && (
                  <p className="text-[11px] text-secondary mt-2">
                    Sample change: {diff.samples.changed[0]}
                  </p>
                )}
              </div>
            ))}
            {diffs.length === 0 && !diffError && (
              <p className="text-xs text-secondary">Select at least two runs with source data to compute parse-tree diffs.</p>
            )}
          </div>
        </div>
      )}
    </motion.section>
  )
}
