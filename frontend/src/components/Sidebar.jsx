function costLevel(score) {
  if (score < 50) return { label: 'Low', color: 'text-green', bg: 'bg-green/10 border-green/40' }
  if (score < 100) return { label: 'Medium', color: 'text-orange', bg: 'bg-orange/10 border-orange/40' }
  return { label: 'High', color: 'text-red', bg: 'bg-red/10 border-red/40' }
}

function StatCard({ label, value }) {
  return (
    <div className="bg-bg rounded-lg p-3 border border-white/10 flex flex-col gap-1">
      <span className="text-secondary text-xs">{label}</span>
      <span className="text-xl font-bold font-mono text-primary">{value}</span>
    </div>
  )
}

export default function Sidebar({ currentStep, data }) {
  const tokenCount = currentStep >= 1 ? data?.token_count ?? 0 : '-'
  const ruleCount = currentStep >= 2 ? data?.rule_count ?? 0 : '-'
  const depth = currentStep >= 2 ? data?.depth ?? 0 : '-'
  const nodeCount = currentStep >= 2 ? data?.node_count ?? 0 : '-'
  const costScore = currentStep >= 3 ? data?.cost_score ?? 0 : '-'
  const level = typeof costScore === 'number' ? costLevel(costScore) : null

  return (
    <aside className="w-full lg:w-72 bg-card border-b lg:border-b-0 lg:border-r border-white/10 p-4 lg:p-5 shrink-0 lg:sticky lg:top-0 lg:h-[calc(100vh-73px)]">
      <div className="sticky top-4 space-y-3">
        <h2 className="text-xs text-secondary uppercase tracking-widest font-semibold">Compiler Snapshot</h2>

        <StatCard label="Token Count" value={tokenCount} />
        <StatCard label="Rule Count" value={ruleCount} />
        <StatCard label="Depth" value={depth} />
        <StatCard label="Node Count" value={nodeCount} />

        <div className={`rounded-lg border p-3 ${level ? level.bg : 'bg-bg border-white/10'}`}>
          <p className="text-xs text-secondary">Cost Score</p>
          <p className={`text-2xl font-bold font-mono mt-1 ${level ? level.color : 'text-primary'}`}>
            {costScore}
          </p>
          <p className={`text-xs mt-1 ${level ? level.color : 'text-secondary'}`}>
            {level ? `${level.label} Complexity` : 'Waiting for metrics phase'}
          </p>
        </div>
      </div>
    </aside>
  )
}
