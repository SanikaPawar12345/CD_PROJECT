import { motion } from 'framer-motion'

function severityStyle(text) {
  const lower = text.toLowerCase()
  if (lower.includes('optimal') || lower.includes('clean'))
    return { border: 'border-green/30',  bg: 'bg-green/10',  icon: '✅', label: 'Optimal',  color: 'text-green'  }
  if (lower.includes('high cost') || lower.includes('deeply nested') || lower.includes('depth'))
    return { border: 'border-danger/30', bg: 'bg-danger/10', icon: '🔴', label: 'High',     color: 'text-danger' }
  return       { border: 'border-orange/30', bg: 'bg-orange/10', icon: '🟡', label: 'Warning', color: 'text-orange' }
}

export default function SuggestionCard({ suggestions }) {
  if (!suggestions || suggestions.length === 0) return null

  return (
    <div className="flex flex-col gap-3">
      <h3 className="text-sm font-semibold text-secondary uppercase tracking-widest">
        Refactoring Suggestions
      </h3>
      {suggestions.map((s, i) => {
        const style = severityStyle(s)
        return (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className={`rounded-xl border ${style.border} ${style.bg} p-4 flex gap-3`}
          >
            <span className="text-base mt-0.5 shrink-0">{style.icon}</span>
            <div>
              <span className={`text-xs font-semibold uppercase tracking-wider ${style.color}`}>
                {style.label}
              </span>
              <p className="text-sm text-primary mt-1 leading-relaxed">{s}</p>
            </div>
          </motion.div>
        )
      })}
    </div>
  )
}
