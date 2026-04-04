import { motion } from 'framer-motion'

function issueTone(text) {
  const message = text.toLowerCase()
  if (message.includes('deep') || message.includes('nest')) return 'text-red border-red/40 bg-red/10'
  if (message.includes('operator') || message.includes('high')) return 'text-orange border-orange/40 bg-orange/10'
  return 'text-cyan border-cyan/40 bg-cyan/10'
}

export default function SuggestionView({ suggestions = [] }) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="bg-card border border-white/10 rounded-xl p-5"
    >
      <h3 className="text-base font-semibold mb-4">Step 4: Suggestions</h3>

      <div className="space-y-3">
        {suggestions.length === 0 && (
          <div className="border border-white/10 rounded-lg p-3 text-secondary text-sm">
            No suggestions returned for this program.
          </div>
        )}

        {suggestions.map((suggestion, index) => (
          <div
            key={`${suggestion}-${index}`}
            className={`rounded-lg border px-4 py-3 text-sm leading-relaxed ${issueTone(suggestion)}`}
          >
            {suggestion}
          </div>
        ))}
      </div>
    </motion.section>
  )
}
