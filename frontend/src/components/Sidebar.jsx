// Color coding thresholds for cost score
function costLevel(score) {
  if (score === null || score === undefined)
    return { label: '–', color: 'text-secondary', border: 'border-secondary/20', bg: 'bg-secondary/10' }
  if (score < 50)
    return { label: 'Low', color: 'text-green',  border: 'border-green/30',  bg: 'bg-green/10'  }
  if (score < 100)
    return { label: 'Medium', color: 'text-orange', border: 'border-orange/30', bg: 'bg-orange/10' }
  return   { label: 'High',   color: 'text-danger', border: 'border-danger/30', bg: 'bg-danger/10' }
}

function StatCard({ label, value, accent }) {
  return (
    <div className={`bg-bg rounded-xl p-4 border border-white/10 flex flex-col gap-1`}>
      <span className="text-secondary text-xs">{label}</span>
      <span className={`text-2xl font-bold font-mono ${accent}`}>
        {value ?? '–'}
      </span>
    </div>
  )
}

export default function Sidebar({ result }) {
  const level = costLevel(result?.cost_score)

  return (
    <aside className="w-64 shrink-0 border-l border-white/10 bg-card p-5 overflow-y-auto flex flex-col gap-4">
      <h2 className="text-sm font-semibold text-secondary uppercase tracking-widest">
        Summary
      </h2>

      <StatCard label="Token Count"  value={result?.token_count} accent="text-cyan" />
      <StatCard label="Rule Count"   value={result?.rule_count}  accent="text-accent" />
      <StatCard label="Parse Depth"  value={result?.max_depth}   accent="text-orange" />
      <StatCard label="Node Count"   value={result?.node_count}  accent="text-primary" />

      {/* Cost Score */}
      <div className={`rounded-xl p-4 border ${level.border} ${level.bg} flex flex-col gap-1`}>
        <span className="text-secondary text-xs">Cost Score</span>
        <span className={`text-3xl font-bold font-mono ${level.color}`}>
          {result?.cost_score ?? '–'}
        </span>
        <span className={`text-xs font-semibold ${level.color} uppercase tracking-wider`}>
          {level.label} Complexity
        </span>
      </div>

      {/* Cost breakdown mini list */}
      {result?.cost_breakdown && (
        <div className="bg-bg rounded-xl p-4 border border-white/10 flex flex-col gap-2">
          <span className="text-secondary text-xs mb-1">Breakdown</span>
          {[
            ['Token ×0.5',  result.cost_breakdown.token_term],
            ['Rules ×1.0',  result.cost_breakdown.rule_term],
            ['Depth ×2.0',  result.cost_breakdown.depth_term],
            ['Nodes ×0.8',  result.cost_breakdown.node_term],
          ].map(([label, val]) => (
            <div key={label} className="flex justify-between text-xs">
              <span className="text-secondary">{label}</span>
              <span className="font-mono text-primary">{val}</span>
            </div>
          ))}
          <div className="border-t border-white/10 pt-2 flex justify-between text-xs font-semibold">
            <span className="text-secondary">Total</span>
            <span className={`font-mono ${level.color}`}>{result.cost_breakdown.total}</span>
          </div>
        </div>
      )}
    </aside>
  )
}
