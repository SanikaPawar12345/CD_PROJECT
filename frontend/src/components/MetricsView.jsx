import {
  Chart as ChartJS,
  CategoryScale, LinearScale, BarElement, ArcElement,
  Title, Tooltip, Legend,
} from 'chart.js'
import { Bar, Doughnut } from 'react-chartjs-2'
import { motion } from 'framer-motion'

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend)

const chartOptions = (title) => ({
  responsive: true,
  plugins: {
    legend: { display: false },
    title: {
      display: true,
      text: title,
      color: '#94A3B8',
      font: { size: 12, weight: '600' },
    },
    tooltip: {
      backgroundColor: '#1E293B',
      titleColor: '#F1F5F9',
      bodyColor: '#94A3B8',
      borderColor: '#3B82F6',
      borderWidth: 1,
    },
  },
  scales: {
    x: {
      grid: { color: '#ffffff10' },
      ticks: { color: '#94A3B8', font: { family: 'JetBrains Mono', size: 11 } },
    },
    y: {
      grid: { color: '#ffffff10' },
      ticks: { color: '#94A3B8', font: { family: 'JetBrains Mono', size: 11 } },
    },
  },
})

function scoreColor(score) {
  if (score < 50) return 'text-green border-green/40 bg-green/10'
  if (score < 100) return 'text-orange border-orange/40 bg-orange/10'
  return 'text-red border-red/40 bg-red/10'
}

export default function MetricsView({
  tokenCount,
  ruleCount,
  depth,
  costScore,
  tokenTypeCount = {},
  ruleBreakdown = {},
  costBreakdown = {},
  phaseTimes = {},
  peakMemoryKb = 0,
  semanticAnalysis = null,
  costOnly = false,
}) {
  const structuralData = {
    labels: ['Tokens', 'Rules', 'Depth'],
    datasets: [{
      label: 'Value',
      data: [tokenCount, ruleCount, depth],
      backgroundColor: ['#3B82F6', '#06B6D4', '#F59E0B'],
      borderRadius: 6,
    }],
  }

  const tokenLabels = Object.keys(tokenTypeCount)
  const tokenValues = Object.values(tokenTypeCount)
  const tokenChartData = {
    labels: tokenLabels.length ? tokenLabels : ['No Data'],
    datasets: [{
      data: tokenValues.length ? tokenValues : [1],
      backgroundColor: ['#06B6D4', '#22C55E', '#F59E0B', '#3B82F6', '#EF4444', '#A855F7', '#14B8A6'],
      borderColor: '#0B1220',
      borderWidth: 1,
    }],
  }

  const topRules = Object.entries(ruleBreakdown)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
  const ruleChartData = {
    labels: topRules.map(([name]) => name),
    datasets: [{
      label: 'Rule Applications',
      data: topRules.map(([, value]) => value),
      backgroundColor: '#06B6D4',
      borderRadius: 6,
    }],
  }

  const rawValues = costBreakdown.raw_values || {}
  const normalizedValues = costBreakdown.normalized_values || {}
  const contributions = costBreakdown.contributions || {}
  const costKeys = ['token', 'depth', 'rules', 'time', 'memory']
  const costLabels = ['Token', 'Depth', 'Rules', 'Time', 'Memory']
  const costData = {
    labels: costLabels,
    datasets: [{
      label: 'Cost Components',
      data: costKeys.map((key) => Number(normalizedValues[key] || 0)),
      backgroundColor: ['#3B82F6', '#06B6D4', '#F59E0B', '#8B5CF6', '#EF4444'],
      borderRadius: 6,
    }],
  }

  const scoreStyle = scoreColor(costScore)
  const contributionItems = [
    { label: 'Token', raw: rawValues.token_count || 0, norm: normalizedValues.token || 0, value: contributions.token_pct || 0, color: 'from-blue-500 to-blue-400' },
    { label: 'Depth', raw: rawValues.depth || 0, norm: normalizedValues.depth || 0, value: contributions.depth_pct || 0, color: 'from-cyan-500 to-sky-400' },
    { label: 'Rules', raw: rawValues.rules || 0, norm: normalizedValues.rules || 0, value: contributions.rules_pct || 0, color: 'from-amber-500 to-orange-400' },
    { label: 'Time', raw: rawValues.time_ms || 0, norm: normalizedValues.time || 0, value: contributions.time_pct || 0, color: 'from-violet-500 to-fuchsia-400' },
    { label: 'Memory', raw: rawValues.memory_kb || 0, norm: normalizedValues.memory || 0, value: contributions.memory_pct || 0, color: 'from-red-500 to-rose-400' },
  ]

  return (
    <motion.section
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="bg-card border border-white/10 rounded-xl p-5"
    >
      <h3 className="text-base font-semibold mb-4">
        {costOnly ? 'Step 3: Cost Calculation' : 'Step 4: Metrics Analysis'}
      </h3>

      {!costOnly && (
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <div className="metrics-surface border border-white/10 rounded-lg p-4">
          <Bar data={structuralData} options={chartOptions('Structural Complexity Metrics')} />
        </div>

        <div className="metrics-surface border border-white/10 rounded-lg p-4 flex items-center justify-center">
          <div className="w-full max-w-[320px]">
            <Doughnut data={tokenChartData} options={chartOptions('Token Type Distribution')} />
          </div>
        </div>

        <div className="metrics-surface border border-white/10 rounded-lg p-4">
          <Bar data={ruleChartData} options={chartOptions('Grammar Rule Breakdown')} />
        </div>

        <div className="metrics-surface border border-white/10 rounded-lg p-4">
          <Bar data={costData} options={chartOptions('Cost Score Components')} />
        </div>

      </div>
      )}

      {costOnly && (
      <div className="mt-4 rounded-lg border border-white/10 p-4 bg-bg/40">
        <h4 className="text-sm font-semibold mb-3 text-primary">Cost Breakdown Panel</h4>
        <div className="space-y-3">
          {contributionItems.map((item) => {
            const percent = Number(item.value || 0)
            const displayWidth = percent > 0 ? Math.max(percent, 4) : 0
            return (
              <div key={item.label} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs gap-3">
                  <span className="text-secondary font-medium">{item.label}</span>
                  <span className="text-primary font-semibold min-w-[3rem] text-right">{percent}%</span>
                </div>
                <div className="flex items-center justify-between text-[11px] text-secondary gap-3">
                  <span>Raw: {typeof item.raw === 'number' ? Number(item.raw).toFixed(item.label === 'Time' || item.label === 'Memory' ? 2 : 0) : item.raw}</span>
                  <span>Normalized: {Number(item.norm || 0).toFixed(3)}</span>
                </div>
                <div className="h-3 rounded-md bg-slate-700/60 border border-white/15 overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${displayWidth}%` }}
                    transition={{ duration: 0.45, ease: 'easeOut' }}
                    className={`h-full bg-gradient-to-r ${item.color} shadow-[0_0_12px_rgba(59,130,246,0.25)]`}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>
      )}

      {costOnly && (
      <div className={`mt-4 border rounded-lg p-4 ${scoreStyle}`}>
        <p className="text-xs uppercase tracking-wide">Cost Score</p>
        <p className="text-3xl font-bold font-mono mt-1">{costScore}</p>
        <p className="text-xs mt-1">Low: green, Moderate: orange, High: red</p>
      </div>
      )}

      {!costOnly && (
        <div className="mt-4 rounded-lg border border-white/10 p-4 bg-bg/40 text-xs grid grid-cols-1 sm:grid-cols-3 gap-2">
          <div>
            <p className="text-secondary">Lexical Time</p>
            <p className="text-primary font-semibold mt-1">{Number(phaseTimes.lexical_ms || 0).toFixed(2)} ms</p>
          </div>
          <div>
            <p className="text-secondary">Parsing Time</p>
            <p className="text-primary font-semibold mt-1">{Number(phaseTimes.parsing_ms || 0).toFixed(2)} ms</p>
          </div>
          <div>
            <p className="text-secondary">Total Time</p>
            <p className="text-primary font-semibold mt-1">{Number(phaseTimes.total_ms || 0).toFixed(2)} ms</p>
          </div>
          <div>
            <p className="text-secondary">Semantic Time</p>
            <p className="text-primary font-semibold mt-1">{Number(phaseTimes.semantic_ms || 0).toFixed(2)} ms</p>
          </div>
          <div>
            <p className="text-secondary">Peak Memory</p>
            <p className="text-primary font-semibold mt-1">{Number(peakMemoryKb || 0).toFixed(2)} KB</p>
          </div>
          <div>
            <p className="text-secondary">Semantic Issues</p>
            <p className="text-primary font-semibold mt-1">{semanticAnalysis?.error_count ?? 0} errors, {semanticAnalysis?.warning_count ?? 0} warnings</p>
          </div>
        </div>
      )}

    </motion.section>
  )
}
