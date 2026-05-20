export interface CostBreakdownPayload {
  raw_values: Record<string, number>
  normalized_values: Record<string, number>
  weights: Record<string, number>
  contributions: Record<string, number>
  total: number
}

export interface SemanticAnalysisPayload {
  symbol_table: Record<string, number[]>
  undefined_variables: string[]
  duplicate_assignments: string[]
  errors: Array<{ type: 'error'; message: string; line: number; column: number }>
  warnings: Array<{ type: 'warning'; message: string; line: number; column: number }>
  error_count: number
  warning_count: number
}

export interface AnalyzeResponse {
  analysis_id: string
  grammar: string
  token_type_count: Record<string, number>
  token_count: number
  rule_count: number
  max_depth: number
  node_count: number
  parse_tree: Record<string, unknown> | null
  parse_tree_summary: string
  parse_tree_node_counts: Record<string, number>
  metrics: Record<string, unknown>
  rule_breakdown: Record<string, number>
  semantic_analysis?: SemanticAnalysisPayload | null
  cost_score: number
  cost_breakdown: CostBreakdownPayload
  suggestions: string[]
  hotspots: Array<Record<string, unknown>>
  phase_times: Record<string, number>
  peak_memory_kb?: number | null
  ai_processing_ms?: number | null
}
