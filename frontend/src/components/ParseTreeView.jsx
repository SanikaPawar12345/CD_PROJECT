import { motion } from 'framer-motion'
import { useMemo, useRef, useState } from 'react'

const NODE_W = 116
const NODE_H = 34
const H_GAP = 34
const V_GAP = 88

function buildGraph(root) {
  if (!root) return { nodes: [], edges: [], width: 0, height: 0 }

  let leafCursor = 0
  const nodes = []
  const edges = []

  function walk(node, depth, path) {
    const children = node.children || []
    let x

    if (children.length === 0) {
      x = leafCursor * (NODE_W + H_GAP)
      leafCursor += 1
    } else {
      const childXs = children.map((child, index) => walk(child, depth + 1, `${path}.${index}`))
      x = (childXs[0] + childXs[childXs.length - 1]) / 2
    }

    const y = depth * V_GAP
    const id = path
    nodes.push({
      id,
      label: node.type || node.value || 'Node',
      terminal: Boolean(node.terminal),
      x,
      y,
      depth,
    })

    children.forEach((_, index) => {
      const childId = `${path}.${index}`
      edges.push({ from: id, to: childId })
    })

    return x
  }

  walk(root, 0, '0')
  nodes.sort((a, b) => a.id.localeCompare(b.id))

  const maxX = Math.max(...nodes.map((node) => node.x), 0)
  const maxY = Math.max(...nodes.map((node) => node.y), 0)

  return {
    nodes,
    edges,
    width: maxX + NODE_W + 40,
    height: maxY + NODE_H + 40,
  }
}

function nodeClass(terminal) {
  if (terminal) return 'fill-green/10 stroke-green/50'
  return 'fill-cyan/10 stroke-cyan/50'
}

export default function ParseTreeView({ parseTree }) {
  const [scale, setScale] = useState(1)
  const [offset, setOffset] = useState({ x: 24, y: 24 })
  const [selectedNodeId, setSelectedNodeId] = useState(null)
  const dragState = useRef({ active: false, x: 0, y: 0 })

  const graph = useMemo(() => buildGraph(parseTree), [parseTree])
  const nodeMap = useMemo(() => Object.fromEntries(graph.nodes.map((node) => [node.id, node])), [graph.nodes])

  function resetView() {
    setScale(1)
    setOffset({ x: 24, y: 24 })
    setSelectedNodeId(null)
  }

  function handleWheel(event) {
    event.preventDefault()
    const direction = event.deltaY > 0 ? -0.08 : 0.08
    setScale((prev) => Math.max(0.35, Math.min(2.2, prev + direction)))
  }

  function handleMouseDown(event) {
    dragState.current = {
      active: true,
      x: event.clientX,
      y: event.clientY,
    }
  }

  function handleMouseMove(event) {
    if (!dragState.current.active) return
    const dx = event.clientX - dragState.current.x
    const dy = event.clientY - dragState.current.y
    dragState.current = { active: true, x: event.clientX, y: event.clientY }
    setOffset((prev) => ({ x: prev.x + dx, y: prev.y + dy }))
  }

  function handleMouseUp() {
    dragState.current.active = false
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="bg-card border border-white/10 rounded-xl p-5 shadow-sm"
    >
      <h3 className="text-base font-semibold mb-4">Step 2: Syntax Analysis (Parse Tree Graph)</h3>

      <div className="flex flex-wrap gap-4 text-xs items-center justify-between">
        <div className="flex gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-cyan/50 border border-cyan/70 inline-block" />
            <span className="text-secondary">Internal Node</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-green/40 border border-green/50 inline-block" />
            <span className="text-secondary">Leaf Node</span>
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setScale((prev) => Math.max(0.35, prev - 0.1))}
            className="px-2 py-1 rounded border border-white/15 text-secondary hover:text-primary"
          >
            Zoom -
          </button>
          <button
            type="button"
            onClick={() => setScale((prev) => Math.min(2.2, prev + 0.1))}
            className="px-2 py-1 rounded border border-white/15 text-secondary hover:text-primary"
          >
            Zoom +
          </button>
          <button
            type="button"
            onClick={resetView}
            className="px-2 py-1 rounded border border-white/15 text-secondary hover:text-primary"
          >
            Reset
          </button>
        </div>
      </div>

      <div
        className="parse-tree-shell mt-4 rounded-xl border border-white/10 shadow-sm h-[30rem] overflow-hidden cursor-grab active:cursor-grabbing"
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {!parseTree && <p className="text-secondary text-sm p-4">No parse tree data available.</p>}

        {parseTree && (
          <svg className="w-full h-full" viewBox={`0 0 ${Math.max(graph.width, 600)} ${Math.max(graph.height, 400)}`}>
            <g transform={`translate(${offset.x}, ${offset.y}) scale(${scale})`}>
              {graph.edges.map((edge) => {
                const from = nodeMap[edge.from]
                const to = nodeMap[edge.to]
                if (!from || !to) return null
                return (
                  <line
                    key={`${edge.from}-${edge.to}`}
                    x1={from.x + NODE_W / 2}
                    y1={from.y + NODE_H}
                    x2={to.x + NODE_W / 2}
                    y2={to.y}
                    className="stroke-white/30"
                    strokeWidth="1.5"
                  />
                )
              })}

              {graph.nodes.map((node) => (
                <g
                  key={node.id}
                  transform={`translate(${node.x}, ${node.y})`}
                  onClick={() => setSelectedNodeId(node.id)}
                  className="cursor-pointer"
                >
                  <rect
                    width={NODE_W}
                    height={NODE_H}
                    rx="8"
                    className={`${nodeClass(node.terminal)} stroke-[1.5] ${selectedNodeId === node.id ? 'stroke-accent' : ''}`}
                  />
                  <text
                    x={NODE_W / 2}
                    y={NODE_H / 2 + 4}
                    textAnchor="middle"
                    fill={node.terminal ? '#14532D' : '#0E7490'}
                    className="text-[11px] font-semibold"
                  >
                    {node.label.length > 16 ? `${node.label.slice(0, 15)}…` : node.label}
                  </text>
                </g>
              ))}
            </g>
          </svg>
        )}
      </div>

      {selectedNodeId && (() => {
        const selected = graph.nodes.find((node) => node.id === selectedNodeId)
        if (!selected) return null
        const childCount = graph.edges.filter((edge) => edge.from === selectedNodeId).length
        return (
          <div className="mt-4 rounded-lg border border-accent/30 bg-accent/10 p-3 text-xs">
            <p className="font-semibold text-primary mb-1">Selected Node Details</p>
            <p className="text-secondary">Node Type: <span className="text-primary font-semibold">{selected.label}</span></p>
            <p className="text-secondary">Depth: <span className="text-primary font-semibold">{selected.depth}</span></p>
            <p className="text-secondary">Children: <span className="text-primary font-semibold">{childCount}</span></p>
          </div>
        )
      })()}
    </motion.section>
  )
}
