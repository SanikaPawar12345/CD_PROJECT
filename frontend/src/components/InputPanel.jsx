import { useEffect, useRef, useState } from 'react'
import Editor from '@monaco-editor/react'

const SAMPLE_CODE = `x = 3 + 4 * 2;
y = x + 1;
print(y);`

const COMPLEX_SAMPLE = `a = 1 + (2 + (3 + (4 + 5)));
b = a * (7 + (8 * (9 + 10)));
print((a + b) + (a * b));`

const CHAINED_SAMPLE = `x = 1 + 2 + 3 + 4 + 5 + 6 + 7;
y = x * 2 * 3 * 4;
print(y);`

export default function InputPanel({
  onAnalyze,
  disabled,
  markers = [],
  hotspots = [],
  grammar = 'default',
  grammarOptions = [],
  onGrammarChange,
  externalCode,
  externalCodeKey,
}) {
  const [code, setCode] = useState(SAMPLE_CODE)
  const fileInputRef = useRef(null)
  const editorRef = useRef(null)
  const monacoRef = useRef(null)

  useEffect(() => {
    if (typeof externalCode === 'string' && externalCode.length > 0) {
      setCode(externalCode)
    }
  }, [externalCodeKey])

  useEffect(() => {
    if (!editorRef.current || !monacoRef.current) return
    const model = editorRef.current.getModel()
    if (!model) return

    const errorMarkers = markers.map((marker) => ({
      startLineNumber: marker.startLineNumber,
      startColumn: marker.startColumn,
      endLineNumber: marker.endLineNumber,
      endColumn: marker.endColumn,
      message: marker.message,
      severity: monacoRef.current.MarkerSeverity.Error,
    }))

    const hotspotMarkers = hotspots
      .filter((hotspot) => hotspot.line)
      .map((hotspot) => ({
        startLineNumber: hotspot.line,
        startColumn: hotspot.column || 1,
        endLineNumber: hotspot.line,
        endColumn: (hotspot.column || 1) + 1,
        message: hotspot.message,
        severity: (hotspot.kind === 'nested-expression' || hotspot.kind === 'deep-recursion')
          ? monacoRef.current.MarkerSeverity.Error
          : monacoRef.current.MarkerSeverity.Warning,
      }))

    monacoRef.current.editor.setModelMarkers(model, 'analysis', [
      ...errorMarkers,
      ...hotspotMarkers,
    ])
  }, [markers, hotspots, code])

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

        <div className="flex gap-2 flex-wrap">
          <button
            type="button"
            onClick={() => setCode(SAMPLE_CODE)}
            className="px-3 py-2 rounded-lg border border-white/15 text-sm text-secondary hover:text-primary hover:border-accent/60 transition"
            disabled={disabled}
          >
            Example: Basic
          </button>
          <button
            type="button"
            onClick={() => setCode(COMPLEX_SAMPLE)}
            className="px-3 py-2 rounded-lg border border-white/15 text-sm text-secondary hover:text-primary hover:border-accent/60 transition"
            disabled={disabled}
          >
            Example: Nested
          </button>
          <button
            type="button"
            onClick={() => setCode(CHAINED_SAMPLE)}
            className="px-3 py-2 rounded-lg border border-white/15 text-sm text-secondary hover:text-primary hover:border-accent/60 transition"
            disabled={disabled}
          >
            Example: Chained
          </button>
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

      <div className="mb-3 flex items-center gap-3">
        <label className="text-xs uppercase tracking-widest text-secondary">Grammar</label>
        <select
          value={grammar}
          onChange={(event) => onGrammarChange?.(event.target.value)}
          className="bg-bg border border-white/15 text-primary text-sm rounded-md px-3 py-1.5"
          disabled={disabled}
        >
          {grammarOptions.map((item) => (
            <option key={item.key} value={item.key}>
              {item.name}
            </option>
          ))}
        </select>
      </div>

      <div className="border border-white/15 rounded-lg overflow-hidden">
        <Editor
          height="320px"
          defaultLanguage="javascript"
          value={code}
          onChange={(value) => setCode(value || '')}
          onMount={(editor, monaco) => {
            editorRef.current = editor
            monacoRef.current = monaco
          }}
          theme="vs-dark"
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            wordWrap: 'on',
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            automaticLayout: true,
          }}
        />
      </div>

      {(markers.length > 0 || hotspots.length > 0) && (
        <div className="mt-3 space-y-2">
          {markers.map((marker, idx) => (
            <div key={`marker-${idx}`} className="text-xs border border-red/40 bg-red/10 text-red rounded px-3 py-2">
              Line {marker.startLineNumber}, Col {marker.startColumn}: {marker.message}
            </div>
          ))}
          {hotspots.slice(0, 3).map((hotspot, idx) => (
            <div key={`hotspot-${idx}`} className="text-xs border border-orange/40 bg-orange/10 text-orange rounded px-3 py-2">
              {hotspot.line ? `Line ${hotspot.line}: ` : ''}{hotspot.message}
            </div>
          ))}
        </div>
      )}

      <div className="mt-4 flex justify-end">
        <button
          type="button"
          onClick={() => onAnalyze(code, grammar)}
          disabled={disabled || !code.trim()}
          className="px-5 py-2.5 rounded-lg bg-accent hover:bg-blue-500 text-white text-sm font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {disabled ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>
    </section>
  )
}
