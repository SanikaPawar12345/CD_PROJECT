import {
  Chart as ChartJS,
  CategoryScale, LinearScale, BarElement,
  Title, Tooltip, Legend,
} from 'chart.js'
import { Bar } from 'react-chartjs-2'
import { motion } from 'framer-motion'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

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

export default function MetricsView({ tokenCount, ruleCount, depth, costScore }) {
  const chartData = {
    labels: ['Tokens', 'Rules', 'Depth'],
    datasets: [{
      label: 'Value',
      data: [tokenCount, ruleCount, depth],
      backgroundColor: ['#3B82F6', '#06B6D4', '#F59E0B'],
      borderRadius: 6,
    }],
  }

  const scoreStyle = scoreColor(costScore)

  return (
    <motion.section
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="bg-card border border-white/10 rounded-xl p-5"
    >
      <h3 className="text-base font-semibold mb-4">Step 3: Metrics and Cost Analysis</h3>

      <div className="bg-bg/40 border border-white/10 rounded-lg p-4">
        <Bar data={chartData} options={chartOptions('Structural Complexity Metrics')} />
      </div>

      <div className={`mt-4 border rounded-lg p-4 ${scoreStyle}`}>
        <p className="text-xs uppercase tracking-wide">Cost Score</p>
        <p className="text-3xl font-bold font-mono mt-1">{costScore}</p>
        <p className="text-xs mt-1">Low: green, Medium: orange, High: red</p>
      </div>
    </motion.section>
  )
}
