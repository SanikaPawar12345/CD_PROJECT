import { motion } from 'framer-motion'

function issueTone(text) {
  const message = text.toLowerCase()
  if (message.includes('deep') || message.includes('nest')) return 'text-red border-red/40 bg-red/10'
  if (message.includes('operator') || message.includes('high')) return 'text-orange border-orange/40 bg-orange/10'
  return 'text-cyan border-cyan/40 bg-cyan/10'
}

function renderList(items = [], emptyText = 'No entries.') {
  if (!Array.isArray(items) || items.length === 0) {
    return <p className="text-secondary text-sm">{emptyText}</p>
  }
  return (
    <ul className="space-y-2">
      {items.map((item, index) => (
        <li key={`${item}-${index}`} className="text-sm text-primary leading-relaxed">
          • {item}
        </li>
      ))}
    </ul>
  )
}

export default function SuggestionView({
  suggestions = [],
  aiEnabled = true,
  aiLoading = false,
  aiError = '',
  aiSuggestions = null,
}) {
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

      <div className="mt-6 border-t border-white/10 pt-5 space-y-4">
        <h4 className="text-sm font-semibold text-secondary uppercase tracking-widest">AI Optimizer Output</h4>

        {!aiEnabled && (
          <div className="rounded-lg border border-white/10 p-3 text-secondary text-sm">
            Enable AI Suggestions to generate Gemini-powered optimization advice.
          </div>
        )}

        {aiEnabled && aiLoading && (
          <div className="rounded-lg border border-cyan/30 bg-cyan/10 p-3 text-cyan text-sm animate-pulse">
            Generating AI optimization suggestions...
          </div>
        )}

        {aiEnabled && !aiLoading && aiError && (
          <div className="rounded-lg border border-red/40 bg-red/10 p-3 text-red text-sm">
            {aiError}
          </div>
        )}

        {aiEnabled && !aiLoading && !aiError && aiSuggestions && (
          <div className="space-y-4">
            <div className="rounded-lg border border-white/10 p-4 bg-bg/40">
              <h5 className="text-xs text-secondary uppercase tracking-widest mb-2">Issues</h5>
              {renderList(aiSuggestions.issues, 'No issues flagged by AI.')}
            </div>

            <div className="rounded-lg border border-white/10 p-4 bg-bg/40">
              <h5 className="text-xs text-secondary uppercase tracking-widest mb-2">Optimizations</h5>
              {renderList(aiSuggestions.optimizations, 'No optimization ideas returned.')}
            </div>

            <div className="rounded-lg border border-accent/30 bg-accent/10 p-4">
              <h5 className="text-xs text-secondary uppercase tracking-widest mb-2">Optimized Code</h5>
              <pre className="text-xs sm:text-sm overflow-auto whitespace-pre-wrap font-mono text-primary bg-bg/70 border border-white/10 rounded p-3">
                {aiSuggestions.optimized_code}
              </pre>
            </div>

            <div className="rounded-lg border border-white/10 p-4 bg-bg/40">
              <h5 className="text-xs text-secondary uppercase tracking-widest mb-2">Explanation</h5>
              <p className="text-sm text-primary leading-relaxed">{aiSuggestions.explanation}</p>
            </div>
          </div>
        )}
      </div>
    </motion.section>
  )
}
