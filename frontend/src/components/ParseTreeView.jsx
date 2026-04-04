import { motion } from 'framer-motion'

function nodeStyle(node) {
  if (node.terminal) return 'bg-green/10 border-green/40 text-green'
  return 'bg-cyan/10 border-cyan/40 text-cyan'
}

function TreeNodeEl({ node, depth = 0 }) {
  const hasChildren = node.children && node.children.length > 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: depth * 0.05, duration: 0.25 }}
      className="flex flex-col items-start"
      style={{ paddingLeft: depth === 0 ? 0 : '1.5rem' }}
    >
      <div
        className={`px-3 py-1 rounded border text-xs font-mono whitespace-nowrap mb-1 ${nodeStyle(node)}`}
      >
        {node.type || node.value || 'Node'}
      </div>

      {hasChildren && (
        <div className="relative pl-4 border-l border-white/15 flex flex-col gap-1 ml-2">
          {node.children.map((child, i) => (
            <TreeNodeEl key={i} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </motion.div>
  )
}

export default function ParseTreeView({ parseTree }) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="bg-card border border-white/10 rounded-xl p-5"
    >
      <h3 className="text-base font-semibold mb-4">Step 2: Syntax Analysis (Parse Tree)</h3>

      <div className="flex gap-4 text-xs">
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-cyan/50 border border-cyan/70 inline-block" />
          <span className="text-secondary">Internal Node</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-green/40 border border-green/50 inline-block" />
          <span className="text-secondary">Leaf Node</span>
        </span>
      </div>

      <div className="mt-4 bg-bg/40 rounded-lg border border-white/10 p-4 overflow-x-auto overflow-y-auto max-h-[28rem]">
        {parseTree ? (
          <TreeNodeEl node={parseTree} depth={0} />
        ) : (
          <p className="text-secondary text-sm">No parse tree data available.</p>
        )}
      </div>
    </motion.section>
  )
}
