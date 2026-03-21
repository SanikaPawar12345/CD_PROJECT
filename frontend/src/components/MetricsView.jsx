import {
  Chart as ChartJS,
  CategoryScale, LinearScale, BarElement,
  Title, Tooltip, Legend,
} from 'chart.js'
import { Bar } from 'react-chartjs-2'
import { motion } from 'framer-motion'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const METRIC_COLORS = ['#3B82F6', '#06B6D4', '#F59E0B', '#22C55E']
const BREAKDOWN_COLORS = ['#3B82F6', '#06B6D4', '#F59E0B', '#EF4444']

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

export default function MetricsView({ metrics, costBreakdown, costScore }) {
  // Bar 1: raw metrics
  const metricsData = {
    labels: ['Token Count', 'Rule Apps', 'Max Depth', 'Nodes'],
    datasets: [{
      label: 'Value',
      data: [
        metrics.token_count,
        metrics.total_rule_applications,
        metrics.max_recursion_depth,
        metrics.parse_tree_nodes,
      ],
      backgroundColor: METRIC_COLORS,
      borderRadius: 6,
    }],
  }

  // Bar 2: cost breakdown
  const breakdownData = {
    labels: ['Token ×0.5', 'Rules ×1.0', 'Depth ×2.0', 'Nodes ×0.8'],
    datasets: [{
      label: 'Cost Term',
      data: [
        costBreakdown.token_term,
        costBreakdown.rule_term,
        costBreakdown.depth_term,
        costBreakdown.node_term,
      ],
      backgroundColor: BREAKDOWN_COLORS,
      borderRadius: 6,
    }],
  }

  // Find the most influential term
  const terms = [
    { name: 'Token Term',  value: costBreakdown.token_term },
    { name: 'Rule Term',   value: costBreakdown.rule_term  },
    { name: 'Depth Term',  value: costBreakdown.depth_term },
    { name: 'Node Term',   value: costBreakdown.node_term  },
  ]
  const top = terms.reduce((a, b) => (a.value >= b.value ? a : b))

  return (
    <div className="flex flex-col gap-6">
      <h3 className="text-sm font-semibold text-secondary uppercase tracking-widest">
        Step 3 — Metrics &amp; Cost
      </h3>

      {/* Highlight most influential */}
      <motion.div
        initial={{ opacity: 0, scale: 0.97 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-orange/10 border border-orange/30 rounded-xl px-5 py-3 flex items-center gap-3"
      >
        <span className="text-orange text-lg">⚡</span>
        <div>
          <p className="text-xs text-secondary">Most Influential Factor</p>
          <p className="text-sm font-semibold text-orange">
            {top.name} — contributes {top.value} pts to total {costScore}
          </p>
        </div>
      </motion.div>

      {/* Rule breakdown mini table */}
      {metrics.rule_breakdown && Object.keys(metrics.rule_breakdown).length > 0 && (
        <div className="bg-card rounded-xl border border-white/10 p-4">
          <p className="text-xs text-secondary font-semibold uppercase tracking-widest mb-3">
            Grammar Rule Applications
          </p>
          <div className="flex flex-wrap gap-2">
            {Object.entries(metrics.rule_breakdown).map(([rule, count]) => (
              <span key={rule} className="px-2.5 py-1 rounded-lg bg-bg border border-white/10 text-xs font-mono">
                <span className="text-cyan">{rule}</span>
                <span className="text-secondary ml-1">×{count}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Two charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-card rounded-xl border border-white/10 p-4">
          <Bar data={metricsData} options={chartOptions('Compiler Metrics')} />
        </div>
        <div className="bg-card rounded-xl border border-white/10 p-4">
          <Bar data={breakdownData} options={chartOptions('Cost Breakdown')} />
        </div>
      </div>
    </div>
  )
}
