import { motion } from 'framer-motion'

// Color per token type
const TYPE_COLORS = {
  ID:     'bg-cyan/20 text-cyan border border-cyan/30',
  NUMBER: 'bg-green/20 text-green border border-green/30',
  PRINT:  'bg-purple-500/20 text-purple-300 border border-purple-500/30',
  ASSIGN: 'bg-orange/20 text-orange border border-orange/30',
  PLUS:   'bg-accent/20 text-accent border border-accent/30',
  STAR:   'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30',
  LPAREN: 'bg-pink-500/20 text-pink-300 border border-pink-500/30',
  RPAREN: 'bg-pink-500/20 text-pink-300 border border-pink-500/30',
  SEMI:   'bg-secondary/20 text-secondary border border-secondary/30',
}
const DEFAULT_COLOR = 'bg-white/10 text-primary border border-white/20'

function typeBadge(type) {
  return TYPE_COLORS[type] || DEFAULT_COLOR
}

// Human-friendly label for each token type in the summary table
const TYPE_LABELS = {
  ID:     'Identifier (ID)',
  NUMBER: 'Number',
  PRINT:  'Keyword: print',
  ASSIGN: 'Assignment (=)',
  PLUS:   'Plus (+)',
  STAR:   'Star (*)',
  LPAREN: 'Left Paren (() ',
  RPAREN: 'Right Paren ())',
  SEMI:   'Semicolon (;)',
}

function typeLabel(type) {
  return TYPE_LABELS[type] || type
}

export default function TokensView({ tokens, tokenTypeCount }) {
  return (
    <div className="flex flex-col gap-4">
      <h3 className="text-sm font-semibold text-secondary uppercase tracking-widest">
        Step 1 — Tokenization
      </h3>

      {/* Two tables side by side */}
      <div className="flex gap-4 items-start flex-wrap lg:flex-nowrap">

        {/* ── Left table: all tokens ── */}
        <div className="flex-1 min-w-0 bg-card rounded-xl border border-white/10 overflow-hidden">
          <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between">
            <span className="text-sm font-semibold text-primary">Token List</span>
            <span className="text-xs font-mono text-secondary bg-bg px-2 py-0.5 rounded-full border border-white/10">
              {tokens.length} tokens
            </span>
          </div>
          <div className="overflow-x-auto max-h-96 overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-card z-10">
                <tr className="border-b border-white/10 text-left">
                  <th className="px-4 py-2 text-secondary font-medium text-xs w-12">#</th>
                  <th className="px-4 py-2 text-secondary font-medium text-xs">Type</th>
                  <th className="px-4 py-2 text-secondary font-medium text-xs">Value</th>
                </tr>
              </thead>
              <tbody>
                {tokens.map((tok, i) => (
                  <motion.tr
                    key={i}
                    initial={{ opacity: 0, x: -12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.03, duration: 0.25 }}
                    className="border-b border-white/5 hover:bg-white/5 transition-colors"
                  >
                    <td className="px-4 py-2 text-secondary font-mono text-xs">{i + 1}</td>
                    <td className="px-4 py-2">
                      <span className={`px-2 py-0.5 rounded text-xs font-mono font-semibold ${typeBadge(tok.type)}`}>
                        {tok.type}
                      </span>
                    </td>
                    <td className="px-4 py-2 font-mono text-xs text-primary">
                      {tok.value || <em className="text-secondary">ε</em>}
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* ── Right table: summary by type ── */}
        <div className="w-72 shrink-0 bg-card rounded-xl border border-white/10 overflow-hidden">
          <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between">
            <span className="text-sm font-semibold text-primary">Token Summary</span>
            <span className="text-xs font-mono text-secondary bg-bg px-2 py-0.5 rounded-full border border-white/10">
              {Object.keys(tokenTypeCount).length} types
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10 text-left">
                  <th className="px-4 py-2 text-secondary font-medium text-xs">Token Type</th>
                  <th className="px-4 py-2 text-secondary font-medium text-xs text-right">Count</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(tokenTypeCount)
                  .sort((a, b) => b[1] - a[1])   // sort by count desc
                  .map(([type, count], i) => (
                    <motion.tr
                      key={type}
                      initial={{ opacity: 0, x: 12 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.07, duration: 0.3 }}
                      className="border-b border-white/5 hover:bg-white/5 transition-colors"
                    >
                      <td className="px-4 py-2.5 flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full shrink-0 ${badgeDot(type)}`} />
                        <span className="text-xs text-primary">{typeLabel(type)}</span>
                      </td>
                      <td className="px-4 py-2.5 text-right">
                        <span className={`font-mono font-bold text-sm ${countColor(count)}`}>
                          {count}
                        </span>
                      </td>
                    </motion.tr>
                  ))}

                {/* Total row */}
                <tr className="border-t border-white/20 bg-bg/40">
                  <td className="px-4 py-2.5 text-xs font-semibold text-secondary">Total</td>
                  <td className="px-4 py-2.5 text-right font-mono font-bold text-primary text-sm">
                    {Object.values(tokenTypeCount).reduce((a, b) => a + b, 0)}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Mini bar chart inside summary */}
          <div className="px-4 pb-4 pt-2 flex flex-col gap-2">
            {Object.entries(tokenTypeCount)
              .sort((a, b) => b[1] - a[1])
              .map(([type, count]) => {
                const max = Math.max(...Object.values(tokenTypeCount))
                const pct = Math.round((count / max) * 100)
                return (
                  <div key={type} className="flex items-center gap-2 text-xs">
                    <span className="w-16 text-right text-secondary font-mono shrink-0">{type}</span>
                    <div className="flex-1 bg-bg rounded-full h-2 overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${pct}%` }}
                        transition={{ duration: 0.5, delay: 0.2 }}
                        className={`h-full rounded-full ${barColor(type)}`}
                      />
                    </div>
                    <span className="w-5 text-right text-primary font-mono font-semibold shrink-0">
                      {count}
                    </span>
                  </div>
                )
              })}
          </div>
        </div>
      </div>
    </div>
  )
}

// Color helpers for the summary table
function badgeDot(type) {
  const map = {
    ID: 'bg-cyan', NUMBER: 'bg-green', PRINT: 'bg-purple-400',
    ASSIGN: 'bg-orange', PLUS: 'bg-accent', STAR: 'bg-yellow-400',
    LPAREN: 'bg-pink-400', RPAREN: 'bg-pink-400', SEMI: 'bg-secondary',
  }
  return map[type] || 'bg-primary'
}

function barColor(type) {
  const map = {
    ID: 'bg-cyan', NUMBER: 'bg-green', PRINT: 'bg-purple-400',
    ASSIGN: 'bg-orange', PLUS: 'bg-accent', STAR: 'bg-yellow-400',
    LPAREN: 'bg-pink-400', RPAREN: 'bg-pink-400', SEMI: 'bg-secondary/60',
  }
  return map[type] || 'bg-primary'
}

function countColor(count) {
  if (count >= 5) return 'text-orange'
  if (count >= 3) return 'text-cyan'
  return 'text-primary'
}
