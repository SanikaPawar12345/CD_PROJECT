import { useRef, useState } from 'react'

const SAMPLE_CODE = `x = 3 + 4 * 2;
y = x + 1;
print(y);`

export default function InputPanel({ onAnalyze, disabled }) {
  const [code, setCode] = useState(SAMPLE_CODE)
  const fileInputRef = useRef(null)

  function handleFileUpload(event) {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (loadEvent) => {
      setCode(String(loadEvent.target?.result || ''))
    }
    reader.readAsText(file)
  }

  return (
    <section className="bg-card border border-white/10 rounded-xl p-5">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
        <h2 className="text-base font-semibold">Step 0: Input Stage</h2>

        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="px-3 py-2 rounded-lg border border-white/15 text-sm text-secondary hover:text-primary hover:border-accent/60 transition"
            disabled={disabled}
          >
            Upload File
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,.c,.cpp,.py,.java"
            className="hidden"
            onChange={handleFileUpload}
          />
        </div>
      </div>

      <textarea
        rows={10}
        value={code}
        onChange={(event) => setCode(event.target.value)}
        spellCheck={false}
        placeholder="Paste your program source here..."
        className="w-full bg-bg border border-white/15 rounded-lg p-4 text-sm font-mono text-primary placeholder:text-secondary/70 focus:outline-none focus:border-accent/70 resize-y"
      />

      <div className="mt-4 flex justify-end">
        <button
          type="button"
          onClick={() => onAnalyze(code)}
          disabled={disabled || !code.trim()}
          className="px-5 py-2.5 rounded-lg bg-accent hover:bg-blue-500 text-white text-sm font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {disabled ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>
    </section>
  )
}
