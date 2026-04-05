export default function HistoryPanel({
  history = [],
  compareIds = [],
  onToggleCompare,
  onStartCompare,
  isCompareMode,
  onReplay,
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-bg/60 p-4 shadow-sm">
      <div className="flex items-start justify-between gap-2 mb-3">
        <div>
          <p className="text-xs uppercase tracking-widest text-secondary font-semibold">Saved Analyses</p>
          <p className="text-[10px] text-secondary">
            {compareIds.length < 2
              ? `Select at least 2 runs (${compareIds.length} selected)`
              : `${compareIds.length} selected. Compare mode ready.`}
          </p>
        </div>
        {compareIds.length >= 2 && !isCompareMode && (
          <button
            type="button"
            onClick={onStartCompare}
            className="px-2 py-1 rounded border border-accent/40 text-[10px] uppercase text-accent hover:bg-accent hover:text-white transition"
          >
            Compare
          </button>
        )}
      </div>

      <div className="space-y-2 max-h-64 overflow-y-auto">
        {history.length === 0 ? (
          <div className="rounded-lg border border-white/10 px-3 py-2 text-xs text-secondary">
            No saved runs yet. Analyze to record history.
          </div>
        ) : (
          history.map((record) => {
            const selected = compareIds.includes(record.id)
            return (
              <div
                key={record.id}
                className={`history-item w-full text-left rounded-xl border px-3 py-2 text-xs transition ${
                  selected
                    ? 'history-item-selected border-cyan/40 bg-cyan/10 text-cyan'
                    : 'border-white/10 bg-card text-secondary hover:border-cyan/40'
                }`}
              >
                <button type="button" onClick={() => onToggleCompare(record.id)} className="w-full text-left">
                  <div className="font-mono text-[11px] text-primary">
                    {new Date(record.createdAt).toLocaleTimeString()}
                  </div>
                  <div className="text-[11px] text-secondary">
                    tokens {record.token_count} · rules {record.rule_count} · depth {record.depth}
                  </div>
                </button>

                <div className="mt-2 pt-2 border-t border-white/10 flex justify-end">
                  <button
                    type="button"
                    onClick={() => onReplay?.(record)}
                    className="px-2 py-1 rounded border border-accent/40 text-[10px] uppercase text-accent hover:bg-accent hover:text-white transition"
                  >
                    Replay Analysis
                  </button>
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
