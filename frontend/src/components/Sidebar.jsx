import HistoryPanel from './HistoryPanel.jsx'

function costLevel(score) {
  if (score < 50) return { label: 'Low', color: 'text-green', bg: 'bg-green/10 border-green/40' }
  if (score < 100) return { label: 'Moderate', color: 'text-orange', bg: 'bg-orange/10 border-orange/40' }
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

export default function Sidebar({
  currentStep,
  data,
  history = [],
  compareIds = [],
  onToggleCompare,
  onStartCompare,
  isCompareMode,
  usageStats,
  onReplay,
}) {
  const tokenCount = currentStep >= 1 ? data?.token_count ?? 0 : '-'
  const ruleCount = currentStep >= 2 ? data?.rule_count ?? 0 : '-'
  const depth = currentStep >= 2 ? data?.depth ?? 0 : '-'
  const nodeCount = currentStep >= 2 ? data?.node_count ?? 0 : '-'
  const costScore = currentStep >= 3 ? data?.cost_score ?? 0 : '-'
  const level = typeof costScore === 'number' ? costLevel(costScore) : null
  const phaseTimes = data?.phase_times || {}
  const analyzeCalls = usageStats?.usage?.analyze_calls ?? '-'
  const syntaxCalls = usageStats?.usage?.syntax_validate_calls ?? '-'
  const cacheHits = usageStats?.usage?.cache_hits ?? '-'
  const cacheMisses = usageStats?.cache?.misses ?? 0
  const cacheHitRate = Number.isFinite(cacheHits) && (Number(cacheHits) + Number(cacheMisses)) > 0
    ? `${Math.round((Number(cacheHits) / (Number(cacheHits) + Number(cacheMisses))) * 100)}%`
    : '-'

  return (
    <aside className="w-full lg:w-80 bg-card border-b lg:border-b-0 lg:border-r border-white/10 p-4 lg:p-5 shrink-0 h-full overflow-y-auto">
      <div className="space-y-3 pb-4">
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

        <div className="rounded-2xl border border-white/10 bg-bg/60 p-4 shadow-sm">
          <p className="text-xs uppercase tracking-widest text-secondary font-semibold mb-2">Execution Time</p>
          <div className="grid grid-cols-1 gap-2 text-xs">
            <div className="rounded-lg border border-white/10 p-2 bg-card">
              <p className="text-secondary">Lexical Analysis</p>
              <p className="text-primary font-semibold mt-0.5">{Number(phaseTimes.lexical_ms || 0).toFixed(2)} ms</p>
            </div>
            <div className="rounded-lg border border-white/10 p-2 bg-card">
              <p className="text-secondary">Parsing</p>
              <p className="text-primary font-semibold mt-0.5">{Number(phaseTimes.parsing_ms || 0).toFixed(2)} ms</p>
            </div>
            <div className="rounded-lg border border-white/10 p-2 bg-card">
              <p className="text-secondary">Total</p>
              <p className="text-primary font-semibold mt-0.5">{Number(phaseTimes.total_ms || 0).toFixed(2)} ms</p>
            </div>
          </div>
        </div>

        {isCompareMode && (
          <div className="rounded-lg border border-accent/40 bg-accent/10 p-3">
            <p className="text-xs uppercase tracking-widest text-accent font-semibold">Comparison Mode Active</p>
          </div>
        )}

        <div className="rounded-2xl border border-white/10 bg-bg/60 p-4 shadow-sm">
          <p className="text-xs uppercase tracking-widest text-secondary font-semibold mb-2">Usage Insights</p>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="rounded-lg border border-white/10 p-2 bg-card">
              <p className="text-secondary">Analyze Calls</p>
              <p className="text-primary font-semibold mt-0.5">{analyzeCalls}</p>
            </div>
            <div className="rounded-lg border border-white/10 p-2 bg-card">
              <p className="text-secondary">Syntax Checks</p>
              <p className="text-primary font-semibold mt-0.5">{syntaxCalls}</p>
            </div>
            <div className="rounded-lg border border-white/10 p-2 bg-card col-span-2">
              <p className="text-secondary">Cache Hit Rate</p>
              <p className="text-primary font-semibold mt-0.5">{cacheHitRate}</p>
            </div>
          </div>
        </div>

        <HistoryPanel
          history={history}
          compareIds={compareIds}
          onToggleCompare={onToggleCompare}
          onStartCompare={onStartCompare}
          isCompareMode={isCompareMode}
          onReplay={onReplay}
        />
      </div>
    </aside>
  )
}
