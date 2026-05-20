import { motion } from 'framer-motion'

function MetricTile({ label, value, hint }) {
  return (
    <div className="rounded-lg border border-white/10 bg-bg/40 p-4">
      <p className="text-secondary text-xs uppercase tracking-widest">{label}</p>
      <p className="text-2xl font-bold font-mono text-primary mt-2">{value}</p>
      {hint && <p className="text-secondary text-xs mt-1">{hint}</p>}
    </div>
  )
}

export default function PerformanceView({ phaseTimes = {}, peakMemoryKb = 0, aiProcessingMs = 0, semanticAnalysis = null }) {
  const semanticMs = Number(phaseTimes.semantic_ms || 0)
  const aiMs = Number(aiProcessingMs || 0)
  const totalMs = Number(phaseTimes.total_ms || 0)

  return (
    <motion.section
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="bg-card border border-white/10 rounded-xl p-5"
    >
      <h3 className="text-base font-semibold mb-4">Performance Metrics</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        <MetricTile label="Lexical Time" value={`${Number(phaseTimes.lexical_ms || 0).toFixed(2)} ms`} />
        <MetricTile label="Parsing Time" value={`${Number(phaseTimes.parsing_ms || 0).toFixed(2)} ms`} />
        <MetricTile label="Semantic Time" value={`${semanticMs.toFixed(2)} ms`} hint={semanticAnalysis ? `${semanticAnalysis.error_count || 0} errors, ${semanticAnalysis.warning_count || 0} warnings` : 'Semantic phase not available'} />
        <MetricTile label="AI Time" value={`${aiMs.toFixed(2)} ms`} hint="Measured on the backend when generating AI suggestions." />
        <MetricTile label="Peak Memory" value={`${Number(peakMemoryKb || 0).toFixed(2)} KB`} />
        <MetricTile label="Total Pipeline Time" value={`${totalMs.toFixed(2)} ms`} hint="End-to-end request duration." />
      </div>
    </motion.section>
  )
}
