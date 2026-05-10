import { motion } from 'framer-motion'

function SeverityPill({ type }) {
  const classes = type === 'error'
    ? 'border-red/40 bg-red/10 text-red'
    : 'border-amber/40 bg-amber/10 text-amber'

  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-semibold uppercase tracking-widest ${classes}`}>
      {type}
    </span>
  )
}

function SectionCard({ title, children }) {
  return (
    <div className="rounded-lg border border-white/10 bg-bg/40 p-4">
      <h4 className="text-xs uppercase tracking-widest text-secondary font-semibold mb-3">{title}</h4>
      {children}
    </div>
  )
}

export default function SemanticView({ semanticAnalysis = null }) {
  const symbolTable = semanticAnalysis?.symbol_table || {}
  const errors = Array.isArray(semanticAnalysis?.errors) ? semanticAnalysis.errors : []
  const warnings = Array.isArray(semanticAnalysis?.warnings) ? semanticAnalysis.warnings : []
  const undefinedVars = Array.isArray(semanticAnalysis?.undefined_variables) ? semanticAnalysis.undefined_variables : []
  const duplicateAssignments = Array.isArray(semanticAnalysis?.duplicate_assignments) ? semanticAnalysis.duplicate_assignments : []

  const symbolEntries = Object.entries(symbolTable)

  return (
    <motion.section
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="bg-card border border-white/10 rounded-xl p-5"
    >
      <h3 className="text-base font-semibold mb-4">Semantic Analysis</h3>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <SectionCard title="Semantic Summary">
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="rounded-lg border border-white/10 bg-card p-3">
              <p className="text-secondary text-xs">Errors</p>
              <p className="text-2xl font-bold font-mono mt-1 text-red">{semanticAnalysis?.error_count ?? 0}</p>
            </div>
            <div className="rounded-lg border border-white/10 bg-card p-3">
              <p className="text-secondary text-xs">Warnings</p>
              <p className="text-2xl font-bold font-mono mt-1 text-amber">{semanticAnalysis?.warning_count ?? 0}</p>
            </div>
          </div>

          <div className="mt-4 space-y-2 text-sm">
            <div>
              <p className="text-secondary text-xs uppercase tracking-widest mb-1">Undeclared Variables</p>
              {undefinedVars.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {undefinedVars.map((name) => (
                    <span key={name} className="rounded-full border border-red/30 bg-red/10 px-2 py-1 text-xs text-red font-mono">{name}</span>
                  ))}
                </div>
              ) : (
                <p className="text-secondary text-sm">None detected.</p>
              )}
            </div>

            <div>
              <p className="text-secondary text-xs uppercase tracking-widest mb-1">Duplicate Assignments</p>
              {duplicateAssignments.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {duplicateAssignments.map((name) => (
                    <span key={name} className="rounded-full border border-amber/30 bg-amber/10 px-2 py-1 text-xs text-amber font-mono">{name}</span>
                  ))}
                </div>
              ) : (
                <p className="text-secondary text-sm">None detected.</p>
              )}
            </div>
          </div>
        </SectionCard>

        <SectionCard title="Symbol Table">
          {symbolEntries.length > 0 ? (
            <div className="space-y-2 max-h-72 overflow-auto pr-1">
              {symbolEntries.map(([name, lines]) => (
                <div key={name} className="rounded-lg border border-white/10 bg-card p-3 flex items-center justify-between gap-3">
                  <div>
                    <p className="font-mono text-primary text-sm">{name}</p>
                    <p className="text-secondary text-xs">Defined on line{Array.isArray(lines) && lines.length > 1 ? 's' : ''} {Array.isArray(lines) ? lines.join(', ') : String(lines)}</p>
                  </div>
                  <SeverityPill type={Array.isArray(lines) && lines.length > 1 ? 'warning' : 'error'} />
                </div>
              ))}
            </div>
          ) : (
            <p className="text-secondary text-sm">No assigned symbols were recorded.</p>
          )}
        </SectionCard>

        <SectionCard title="Warnings and Errors">
          <div className="space-y-3 max-h-72 overflow-auto pr-1">
            {errors.length === 0 && warnings.length === 0 && (
              <p className="text-secondary text-sm">No semantic issues found.</p>
            )}
            {errors.map((entry, index) => (
              <div key={`error-${index}`} className="rounded-lg border border-red/30 bg-red/10 p-3 text-sm text-primary">
                <div className="flex items-center justify-between gap-2 mb-1">
                  <span className="font-semibold text-red">{entry.message}</span>
                  <SeverityPill type="error" />
                </div>
                <p className="text-secondary text-xs">Line {entry.line}, Column {entry.column}</p>
              </div>
            ))}
            {warnings.map((entry, index) => (
              <div key={`warning-${index}`} className="rounded-lg border border-amber/30 bg-amber/10 p-3 text-sm text-primary">
                <div className="flex items-center justify-between gap-2 mb-1">
                  <span className="font-semibold text-amber">{entry.message}</span>
                  <SeverityPill type="warning" />
                </div>
                <p className="text-secondary text-xs">Line {entry.line}, Column {entry.column}</p>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Assignments">
          {symbolEntries.length > 0 ? (
            <div className="space-y-2 text-sm">
              {symbolEntries.map(([name, lines]) => (
                <div key={`assign-${name}`} className="rounded-lg border border-white/10 bg-card p-3">
                  <p className="font-mono text-primary text-sm">{name}</p>
                  <p className="text-secondary text-xs mt-1">Assignment tracking: {Array.isArray(lines) ? lines.length : 1} definition(s)</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-secondary text-sm">No assignments tracked for this input.</p>
          )}
        </SectionCard>
      </div>
    </motion.section>
  )
}
