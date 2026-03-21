import { motion } from 'framer-motion'

// Terminal nodes have no children; non-terminals do.
function nodeStyle(node) {
  if (node.terminal) {
    // leaf / terminal
    return 'bg-green/20 border-green/40 text-green'
  }
  // internal / non-terminal
  return 'bg-accent/20 border-accent/40 text-accent'
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
      {/* Node pill */}
      <div
        className={`px-3 py-1 rounded-lg border text-xs font-mono font-semibold
                    whitespace-nowrap mb-1 ${nodeStyle(node)}`}
      >
        {node.type}
      </div>

      {/* Children */}
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

export default function ParseTreeView({ tree }) {
  return (
    <div className="flex flex-col gap-4">
      <h3 className="text-sm font-semibold text-secondary uppercase tracking-widest">
        Step 2 — Parse Tree
      </h3>

      {/* Legend */}
      <div className="flex gap-4 text-xs">
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-accent/40 border border-accent/50 inline-block" />
          <span className="text-secondary">Non-Terminal</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-green/40 border border-green/50 inline-block" />
          <span className="text-secondary">Terminal (Leaf)</span>
        </span>
      </div>

      <div className="bg-card rounded-xl border border-white/10 p-6 overflow-x-auto overflow-y-auto max-h-[28rem]">
        {tree ? (
          <TreeNodeEl node={tree} depth={0} />
        ) : (
          <p className="text-secondary text-sm">No parse tree available.</p>
        )}
      </div>
    </div>
  )
}
