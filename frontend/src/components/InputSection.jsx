import { useState, useRef } from 'react'
import { motion } from 'framer-motion'

const PLACEHOLDER = `x = 3 + 4 * 2;
y = x + 1;
print(y);`

export default function InputSection({ onAnalyze, loading }) {
  const [code, setCode] = useState(PLACEHOLDER)
  const fileRef = useRef()

  function handleFile(e) {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = ev => setCode(ev.target.result)
    reader.readAsText(file)
  }

  return (
    <div className="bg-card rounded-2xl border border-white/10 p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-primary">Source Program</h2>
        <button
          onClick={() => fileRef.current?.click()}
          className="text-xs text-secondary hover:text-cyan border border-white/10 hover:border-cyan/40
                     px-3 py-1.5 rounded-lg transition-all"
        >
          Upload .txt
        </button>
        <input ref={fileRef} type="file" accept=".txt" className="hidden" onChange={handleFile} />
      </div>

      <textarea
        value={code}
        onChange={e => setCode(e.target.value)}
        rows={8}
        spellCheck={false}
        className="w-full bg-bg border border-white/10 rounded-xl p-4 text-sm font-mono
                   text-primary resize-none outline-none focus:border-accent/60 transition-colors"
        placeholder="Paste or type your program here…"
      />

      <motion.button
        onClick={() => onAnalyze(code)}
        disabled={loading || !code.trim()}
        whileTap={{ scale: 0.97 }}
        className="self-end px-6 py-2.5 rounded-xl bg-accent hover:bg-blue-500 text-white
                   font-semibold text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed
                   shadow-lg shadow-accent/20"
      >
        {loading ? 'Analyzing…' : 'Analyze'}
      </motion.button>
    </div>
  )
}
