import { motion } from 'framer-motion'
import { useEffect, useRef, useState } from 'react'
import axios from 'axios'
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, BarElement,
  Title, Tooltip, Legend,
} from 'chart.js'
import { Bar } from 'react-chartjs-2'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

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
  const [reportLoading, setReportLoading] = useState(false)
  const baseline = records[0]
  const compareChartRef = useRef(null)
  const costCompareRef = useRef(null)

  const compareLabels = ['Tokens', 'Rules', 'Depth', 'Nodes', 'Cost', 'Total ms', 'Peak KB']
  const baselineData = baseline
    ? [
        Number(baseline.token_count || 0),
        Number(baseline.rule_count || 0),
        Number(baseline.depth || 0),
        Number(baseline.node_count || 0),
        Number(baseline.cost_score || 0),
        Number(baseline.analysis_payload?.phase_times?.total_ms || 0),
        Number(baseline.analysis_payload?.peak_memory_kb || 0),
      ]
    : []
  const target = records[1]
  const targetData = target
    ? [
        Number(target.token_count || 0),
        Number(target.rule_count || 0),
        Number(target.depth || 0),
        Number(target.node_count || 0),
        Number(target.cost_score || 0),
        Number(target.analysis_payload?.phase_times?.total_ms || 0),
        Number(target.analysis_payload?.peak_memory_kb || 0),
      ]
    : []

  const comparisonChartData = {
    labels: compareLabels,
    datasets: [
      {
        label: programLabel(0),
        data: baselineData,
        backgroundColor: '#3B82F6',
        borderRadius: 6,
      },
      ...(target ? [{
        label: programLabel(1),
        data: targetData,
        backgroundColor: '#F59E0B',
        borderRadius: 6,
      }] : []),
    ],
  }

  const baselineCost = baseline?.analysis_payload?.cost_breakdown?.contributions || {}
  const targetCost = target?.analysis_payload?.cost_breakdown?.contributions || {}
  const costLabels = ['Token', 'Rules', 'Depth', 'Time', 'Memory']
  const costCompareData = {
    labels: costLabels,
    datasets: [
      {
        label: programLabel(0),
        data: [
          Number(baselineCost.token_pct || 0),
          Number(baselineCost.rules_pct || 0),
          Number(baselineCost.depth_pct || 0),
          Number(baselineCost.time_pct || 0),
          Number(baselineCost.memory_pct || 0),
        ],
        backgroundColor: '#3B82F6',
        borderRadius: 6,
      },
      ...(target ? [{
        label: programLabel(1),
        data: [
          Number(targetCost.token_pct || 0),
          Number(targetCost.rules_pct || 0),
          Number(targetCost.depth_pct || 0),
          Number(targetCost.time_pct || 0),
          Number(targetCost.memory_pct || 0),
        ],
        backgroundColor: '#F59E0B',
        borderRadius: 6,
      }] : []),
    ],
  }

  function pctReduction(base, next) {
    if (!base || base <= 0) return 0
    return Math.round(((base - next) / base) * 1000) / 10
  }

  const tokenReduction = pctReduction(baseline?.token_count, target?.token_count)
  const nodeReduction = pctReduction(baseline?.node_count, target?.node_count)
  const costReduction = pctReduction(baseline?.cost_score, target?.cost_score)
  const timeReduction = pctReduction(
    baseline?.analysis_payload?.phase_times?.total_ms,
    target?.analysis_payload?.phase_times?.total_ms,
  )
  const memoryReduction = pctReduction(
    baseline?.analysis_payload?.peak_memory_kb,
    target?.analysis_payload?.peak_memory_kb,
  )
  const originalAi = records[0]?.analysis_payload?.ai_suggestions || null
  const optimizedAi = records[1]?.analysis_payload?.ai_suggestions || null

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

      <div className="mb-4">
        <button
          type="button"
          onClick={async () => {
            try {
              setReportLoading(true)
              const chartImage = compareChartRef.current?.toBase64Image?.()
              const costChart = costCompareRef.current?.toBase64Image?.()
              const images = [
                ...(chartImage ? [{ name: 'comparison_overview.png', data: chartImage }] : []),
                ...(costChart ? [{ name: 'comparison_cost_breakdown.png', data: costChart }] : []),
              ]
              const comparisonSummary = {
                baseline: {
                  id: records[0]?.id || null,
                  grammar: records[0]?.grammar || 'default',
                  token_count: records[0]?.token_count || 0,
                  rule_count: records[0]?.rule_count || 0,
                  depth: records[0]?.depth || 0,
                  node_count: records[0]?.node_count || 0,
                  cost_score: records[0]?.cost_score || 0,
                  total_ms: records[0]?.analysis_payload?.phase_times?.total_ms || 0,
                  peak_memory_kb: records[0]?.analysis_payload?.peak_memory_kb || 0,
                },
                optimized: records[1]
                  ? {
                      id: records[1]?.id || null,
                      grammar: records[1]?.grammar || 'default',
                      token_count: records[1]?.token_count || 0,
                      rule_count: records[1]?.rule_count || 0,
                      depth: records[1]?.depth || 0,
                      node_count: records[1]?.node_count || 0,
                      cost_score: records[1]?.cost_score || 0,
                      total_ms: records[1]?.analysis_payload?.phase_times?.total_ms || 0,
                      peak_memory_kb: records[1]?.analysis_payload?.peak_memory_kb || 0,
                    }
                  : null,
                parse_tree_diffs: diffs,
              }
              const payload = {
                original_code: records[0]?.source_code || '',
                optimized_code: records[1]?.source_code || '',
                original_analysis: records[0]?.analysis_payload || null,
                optimized_analysis: records[1]?.analysis_payload || null,
                comparison: comparisonSummary,
                ai_suggestions: records[1]?.analysis_payload?.ai_suggestions || null,
                images,
              }
              console.info('[report] starting comparison export', { images: images.length })
              const resp = await axios.post(`${API_BASE}/export-report`, payload, { responseType: 'blob' })
              const disposition = resp.headers?.['content-disposition'] || ''
              const filenameMatch = /filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i.exec(disposition)
              const filename = decodeURIComponent(filenameMatch?.[1] || filenameMatch?.[2] || '')
                || `comparison-report-${Date.now()}.zip`
              const blobUrl = URL.createObjectURL(resp.data)
              const anchor = document.createElement('a')
              anchor.href = blobUrl
              anchor.download = filename
              document.body.appendChild(anchor)
              anchor.click()
              anchor.remove()
              URL.revokeObjectURL(blobUrl)
              console.info('[report] comparison export complete', { filename })
            } catch (e) {
              console.error('[report] comparison export failed', e)
              alert('Failed to generate report on server.')
            } finally {
              setReportLoading(false)
            }
          }}
          className="px-3 py-2 rounded-lg border border-white/15 text-sm text-secondary hover:text-primary disabled:opacity-60"
          disabled={reportLoading}
        >
          {reportLoading ? 'Generating Report...' : 'Download Report'}
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
        <div className="mt-6 rounded-xl border border-white/10 bg-bg/50 p-4">
          <h3 className="text-sm font-semibold text-primary mb-3">Reduction Summary</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 text-sm">
            <div className="rounded-lg border border-white/10 bg-card p-3">
              <p className="text-xs text-secondary">Token Reduction</p>
              <p className="text-lg font-semibold text-primary">{tokenReduction}%</p>
            </div>
            <div className="rounded-lg border border-white/10 bg-card p-3">
              <p className="text-xs text-secondary">Node Reduction</p>
              <p className="text-lg font-semibold text-primary">{nodeReduction}%</p>
            </div>
            <div className="rounded-lg border border-white/10 bg-card p-3">
              <p className="text-xs text-secondary">Cost Reduction</p>
              <p className="text-lg font-semibold text-primary">{costReduction}%</p>
            </div>
            <div className="rounded-lg border border-white/10 bg-card p-3">
              <p className="text-xs text-secondary">Time Reduction</p>
              <p className="text-lg font-semibold text-primary">{timeReduction}%</p>
            </div>
            <div className="rounded-lg border border-white/10 bg-card p-3">
              <p className="text-xs text-secondary">Memory Reduction</p>
              <p className="text-lg font-semibold text-primary">{memoryReduction}%</p>
            </div>
          </div>
        </div>
      )}

      {records.length >= 2 && (
        <div className="mt-6 rounded-xl border border-white/10 bg-bg/50 p-4">
          <h3 className="text-sm font-semibold text-primary mb-3">Execution Time Comparison</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 text-sm">
            <div className="rounded-lg border border-white/10 bg-card p-3">
              <p className="text-xs text-secondary">Lexical (ms)</p>
              <p className="text-primary">{Number(baseline?.analysis_payload?.phase_times?.lexical_ms || 0).toFixed(2)} → {Number(target?.analysis_payload?.phase_times?.lexical_ms || 0).toFixed(2)}</p>
            </div>
            <div className="rounded-lg border border-white/10 bg-card p-3">
              <p className="text-xs text-secondary">Parsing (ms)</p>
              <p className="text-primary">{Number(baseline?.analysis_payload?.phase_times?.parsing_ms || 0).toFixed(2)} → {Number(target?.analysis_payload?.phase_times?.parsing_ms || 0).toFixed(2)}</p>
            </div>
            <div className="rounded-lg border border-white/10 bg-card p-3">
              <p className="text-xs text-secondary">Semantic (ms)</p>
              <p className="text-primary">{Number(baseline?.analysis_payload?.phase_times?.semantic_ms || 0).toFixed(2)} → {Number(target?.analysis_payload?.phase_times?.semantic_ms || 0).toFixed(2)}</p>
            </div>
            <div className="rounded-lg border border-white/10 bg-card p-3">
              <p className="text-xs text-secondary">AI (ms)</p>
              <p className="text-primary">{Number(baseline?.analysis_payload?.ai_processing_ms || 0).toFixed(2)} → {Number(target?.analysis_payload?.ai_processing_ms || 0).toFixed(2)}</p>
            </div>
            <div className="rounded-lg border border-white/10 bg-card p-3">
              <p className="text-xs text-secondary">Total (ms)</p>
              <p className="text-primary">{Number(baseline?.analysis_payload?.phase_times?.total_ms || 0).toFixed(2)} → {Number(target?.analysis_payload?.phase_times?.total_ms || 0).toFixed(2)}</p>
            </div>
            <div className="rounded-lg border border-white/10 bg-card p-3">
              <p className="text-xs text-secondary">Peak Memory (KB)</p>
              <p className="text-primary">{Number(baseline?.analysis_payload?.peak_memory_kb || 0).toFixed(2)} → {Number(target?.analysis_payload?.peak_memory_kb || 0).toFixed(2)}</p>
            </div>
          </div>
        </div>
      )}

      {records.length >= 2 && (
        <div className="mt-6 rounded-xl border border-white/10 bg-bg/50 p-4">
          <h3 className="text-sm font-semibold text-primary mb-3">Comparison Overview</h3>
          <Bar
            ref={compareChartRef}
            data={comparisonChartData}
            options={{
              responsive: true,
              plugins: {
                legend: { labels: { color: '#94A3B8' } },
                title: { display: true, text: 'Side-by-Side Metrics', color: '#94A3B8', font: { size: 12, weight: '600' } },
              },
              scales: {
                x: { ticks: { color: '#94A3B8' }, grid: { color: '#ffffff10' } },
                y: { ticks: { color: '#94A3B8' }, grid: { color: '#ffffff10' } },
              },
            }}
          />
        </div>
      )}

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

      {records.length >= 2 && (
        <div className="mt-6 rounded-xl border border-white/10 bg-bg/50 p-4">
          <h3 className="text-sm font-semibold text-primary mb-3">Cost Breakdown Comparison</h3>
          <Bar
            ref={costCompareRef}
            data={costCompareData}
            options={{
              responsive: true,
              plugins: {
                legend: { labels: { color: '#94A3B8' } },
                title: { display: true, text: 'Cost Contribution (%)', color: '#94A3B8', font: { size: 12, weight: '600' } },
              },
              scales: {
                x: { ticks: { color: '#94A3B8' }, grid: { color: '#ffffff10' } },
                y: { ticks: { color: '#94A3B8' }, grid: { color: '#ffffff10' } },
              },
            }}
          />
        </div>
      )}

      {records.length >= 2 && (originalAi || optimizedAi) && (
        <div className="mt-6 rounded-xl border border-white/10 bg-bg/50 p-4">
          <h3 className="text-sm font-semibold text-primary mb-3">AI Optimization Summary</h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 text-sm">
            <div className="rounded-lg border border-white/10 bg-card p-3">
              <p className="text-xs text-secondary uppercase tracking-widest">Original</p>
              {(originalAi?.issues || []).length === 0
                ? <p className="text-secondary text-sm mt-2">No AI issues captured.</p>
                : (
                  <ul className="mt-2 space-y-1">
                    {(originalAi?.issues || []).slice(0, 3).map((item, idx) => (
                      <li key={`orig-ai-${idx}`} className="text-primary">• {item}</li>
                    ))}
                  </ul>
                )}
            </div>
            <div className="rounded-lg border border-white/10 bg-card p-3">
              <p className="text-xs text-secondary uppercase tracking-widest">Optimized</p>
              {(optimizedAi?.optimizations || []).length === 0
                ? <p className="text-secondary text-sm mt-2">No AI optimizations captured.</p>
                : (
                  <ul className="mt-2 space-y-1">
                    {(optimizedAi?.optimizations || []).slice(0, 3).map((item, idx) => (
                      <li key={`opt-ai-${idx}`} className="text-primary">• {item}</li>
                    ))}
                  </ul>
                )}
            </div>
          </div>
        </div>
      )}
    </motion.section>
  )
}
