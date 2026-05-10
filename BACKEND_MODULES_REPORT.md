# Backend Implementation Mapping for Compiler Dashboard Modules

Date: 2026-05-11

This document explains backend behavior for each frontend module using only code present in this repository. It is written in simple language for viva preparation.


## 0) Backend architecture overview (high level)

Main entry:
- api.py (FastAPI app, routes, orchestration, logging, caching, AI)

Core compiler pipeline:
- src/lexer.py (tokenization)
- src/parser.py (recursive descent parsing)
- src/tree.py (parse tree nodes)
- src/metrics.py (metrics collection)
- src/semantic.py (semantic analysis)
- src/cost.py (cost scoring and breakdown)
- src/advisor.py (rule-based suggestions)
- src/config.py (weights, thresholds, normalization)
- src/grammars/* (grammar registry and grammar-specific tokenization/parsing)

Shared data structures:
- Token class in src/lexer.py
- TreeNode class in src/tree.py
- Metrics class in src/metrics.py
- Pydantic models in api.py for request/response

Main API routes used by frontend:
- POST /analyze
- POST /validate-syntax
- POST /ai-suggestions
- GET /grammars
- GET /grammar-rules
- POST /parse-tree-diff (used in compare view)


## 1) TOKENIZATION (Frontend: Tokenization tab)

### 1) Backend files involved
- src/lexer.py
- src/grammars/default.py
- src/grammars/c.py
- src/grammars/regex.py
- src/grammars/__init__.py
- api.py

### 2) Functions and classes used
- src/lexer.py: Token, tokenize(), TOKEN_SPEC, MASTER_RE
- src/grammars/default.py: DefaultExpressionGrammar.tokenize()
- src/grammars/c.py: c_tokenize(), CGrammar.tokenize()
- src/grammars/regex.py: regex_tokenize(), RegexGrammar.tokenize()
- src/grammars/__init__.py: get_grammar(), list_grammars()
- api.py: _run_analysis_cached(), token_type_summary()

### 3) API routes connected
- POST /analyze
- POST /validate-syntax

### 4) Data flow
Frontend input
-> POST /analyze (code, grammar, analysis_level)
-> resolve_grammar_or_400() -> grammar.tokenize(source)
-> Token list built in lexer
-> token list converted to dicts
-> returned as tokens[] + token_type_count + token_count

### 5) Step-by-step execution flow
1. api.py: analyze() resolves source and grammar.
2. api.py: validate_input_by_grammar() checks syntax format per grammar.
3. api.py: _run_analysis_cached() calls grammar.tokenize().
4. Lexer returns a list of Token objects.
5. api.py converts Token objects to dicts (type, value, line, column).
6. api.py also computes token_type_count with token_type_summary().
7. Response includes tokens and counts for frontend rendering.

### 6) Input and output structure
Input (POST /analyze):
- source_code or code (string)
- grammar (string: default, c, regex)
- analysis_level (tokens, syntax, full)

Output fields used by frontend:
- tokens: list of {type, value, line, column}
- token_type_count: dict token_type -> count
- token_count: integer

### 7) How frontend communicates with backend
- Frontend sends a JSON payload to POST /analyze.
- The backend returns the token list and summary counts as JSON.

### 8) What logic is implemented
- Manual regex tokenization for default and C grammars.
- Manual character-based tokenization for regex grammar.
- Keyword promotion ("print" becomes PRINT) in src/lexer.py.

### 9) How results are generated
- Regular expressions match tokens in source order.
- Each match becomes a Token with line/column data.
- EOF token is appended for parser use (not sent to frontend).

### 10) Data structures used
- Token class (type, value, line, column, position)
- List of Token objects
- token_type_count dict

### 11) Algorithms used
- Regex scanning with a master regex (default, C).
- Single pass character scanning (regex grammar).

### 12) Time complexity
- Default/C lexer: O(n) over source length, single regex scan.
- Regex lexer: O(n) single character scan.

### 13) Dependencies/libraries used
- Python re module (regex matching) in lexer and C grammar.
- No external lexer libraries are used.

### 14) Why those libraries are used
- re provides simple pattern matching for tokens with minimal code.

### 15) Important code blocks (what they do)
- src/lexer.py TOKEN_SPEC and MASTER_RE: define token patterns and build a single combined regex.
- src/lexer.py tokenize(): iterates matches, ignores SKIP/COMMENT, raises SyntaxError on MISMATCH, adds EOF.
- src/grammars/c.py c_tokenize(): same pattern with C-specific tokens.
- src/grammars/regex.py regex_tokenize(): manual char scanning for regex operators.

### Tokenization specific answers
- Lexer file used: src/lexer.py (default grammar) or src/grammars/c.py and src/grammars/regex.py.
- Regex tokenization: uses MASTER_RE with named groups for each token type in default and C grammar.
- Token generation: each regex match creates a Token object with line/column/position.
- Token structure: type, value, line, column, position.
- Token types: defined in TOKEN_SPEC (default) or C_TOKEN_SPEC (C) or regex operators (RegexGrammar).
- Error handling: MISMATCH raises SyntaxError with line/column.
- Tokens returned to frontend: token list is converted to dicts in api.py.
- Hardcoded token definitions: TOKEN_SPEC, C_TOKEN_SPEC, and regex operators are hardcoded.
- Lexer libraries: None. Manual implementation only.


## 2) PARSE TREE (Frontend: Parse Tree tab)

### 1) Backend files involved
- src/parser.py
- src/tree.py
- src/metrics.py
- src/grammars/default.py
- src/grammars/c.py
- src/grammars/regex.py
- api.py

### 2) Functions and classes used
- src/parser.py: Parser, CLikeParser, RegexParser, parse_* methods
- src/tree.py: TreeNode
- src/metrics.py: Metrics.record_rule(), Metrics.summary()
- api.py: tree_to_dict(), summarize_parse_tree(), parse_tree_node_counts(), _run_analysis_cached()

### 3) API routes connected
- POST /analyze
- POST /parse-tree-diff (compare view)

### 4) Data flow
Frontend input
-> POST /analyze
-> grammar.parse_with_metrics(tokens)
-> parser.parse() builds TreeNode tree
-> api.py tree_to_dict() serializes to JSON
-> response includes parse_tree, parse_tree_summary, parse_tree_node_counts

### 5) Step-by-step execution flow
1. api.py calls grammar.parse_with_metrics(tokens).
2. Grammar creates parser instance (Parser, CLikeParser, or RegexParser).
3. parser.parse() calls parse_program() as the root.
4. Each parse_* method builds TreeNode and consumes tokens.
5. Metrics.record_rule() called at start of each parse_* method.
6. api.py converts TreeNode to dict using tree_to_dict().
7. api.py computes summary string and node counts.

### 6) Input and output structure
Input: list of Token objects from lexer.
Output (analyze response):
- parse_tree: nested dict {type, terminal, children}
- parse_tree_summary: string
- parse_tree_node_counts: dict {internal, leaf, total}

### 7) How frontend communicates with backend
- Frontend calls POST /analyze with visualization=true.
- Backend returns parse_tree JSON for rendering.

### 8) What logic is implemented
- Hand-written recursive descent parser.
- Grammar rules are hardcoded as parse_* methods in src/parser.py.
- Supports three grammars: default expression, C subset, regex.

### 9) How results are generated
- Each parse rule creates TreeNode with the rule name.
- Terminal nodes are TreeNode with literal labels (for tokens).
- Children are added in parsing order.

### 10) Data structures used
- TreeNode (label + children list)
- Token list
- Metrics rule count and depth tracking

### 11) Algorithms used
- Recursive descent parsing with right-recursive or iterative tails.
- Parsing complexity is linear for this grammar in typical cases, O(n).

### 12) Time complexity
- Parser: O(n) for valid input, where n is token count.
- Node counting: O(m) where m is number of nodes (tree size).

### 13) Dependencies/libraries used
- No external parsing library.
- Standard Python only.

### 14) Why those libraries are used
- Manual parsing is simpler for educational grammar and keeps dependencies small.

### 15) Important code blocks (what they do)
- src/parser.py parse_program/parse_statement_list/etc: implement grammar rules.
- src/parser.py consume(): checks expected token and advances.
- src/tree.py TreeNode: simple parse tree node with children.
- api.py tree_to_dict(): converts TreeNode to JSON for frontend.

### Parse tree specific answers
- Parser files: src/parser.py plus grammar wrappers in src/grammars/*.py.
- Recursive descent: each parse_* method calls others based on grammar (see Parser.parse_expr, parse_term, parse_factor, etc).
- Grammar rules: hardcoded in parse_* methods and also listed in grammar classes in src/grammars/*.py.
- Node creation: TreeNode created for each rule and terminal.
- Tree data structure: TreeNode with children list, serialized to dict.
- Traversal: tree_to_dict does a recursive traversal (preorder).
- Visualization: frontend uses parse_tree JSON from /analyze response.


## 3) SEMANTIC ANALYSIS (Frontend: Semantic Analysis tab)

### 1) Backend files involved
- src/semantic.py
- api.py

### 2) Functions and classes used
- src/semantic.py: SemanticAnalyzer, SemanticError
- api.py: _run_analysis_cached() calls SemanticAnalyzer.analyze()

### 3) API routes connected
- POST /analyze

### 4) Data flow
Frontend input
-> POST /analyze
-> SemanticAnalyzer(source).analyze()
-> semantic_analysis dict added to response

### 5) Step-by-step execution flow
1. api.py: _run_analysis_cached() creates SemanticAnalyzer(source).
2. SemanticAnalyzer.analyze() runs three passes:
   - _build_symbol_table()
   - _detect_undeclared_variables()
   - _detect_duplicate_assignments()
3. Results are packaged into a dict and returned.

### 6) Input and output structure
Input: source code string.
Output (semantic_analysis dict):
- symbol_table: {var_name: [line_numbers]}
- undefined_variables: list of names
- duplicate_assignments: list of names
- errors: list of {type, message, line, column}
- warnings: list of {type, message, line, column}
- error_count, warning_count

### 7) How frontend communicates with backend
- Frontend gets semantic_analysis inside /analyze response.

### 8) What logic is implemented
- Simple symbol table (variables assigned on LHS of '=').
- Undeclared variable detection in RHS expressions.
- Warning for duplicate assignment (reassignment) after first definition.
- Reserved words are ignored (print, int, etc).

### 9) How results are generated
- Regex-based pattern matching on source lines.
- Errors and warnings stored as SemanticError objects then converted to dicts.

### 10) Data structures used
- symbol_table dict (name -> list of line numbers)
- SemanticError objects
- lists for errors and warnings

### 11) Algorithms used
- Three linear passes over lines with regex matching.

### 12) Time complexity
- O(n) over number of lines and characters.

### 13) Dependencies/libraries used
- Python re module.
- No external semantic analysis libraries.

### 14) Why those libraries are used
- re is enough for this lightweight, educational semantic analysis.

### 15) Important code blocks (what they do)
- SemanticAnalyzer._build_symbol_table(): captures assignments.
- SemanticAnalyzer._detect_undeclared_variables(): finds undeclared uses in RHS.
- SemanticAnalyzer._detect_duplicate_assignments(): warns about reassignment.

### What is NOT implemented
- No full type checking.
- No scope nesting model (single flat symbol table).
- No control-flow analysis or data-flow analysis.
- No complex type inference.


## 4) METRICS (Frontend: Metrics tab)

### 1) Backend files involved
- src/metrics.py
- src/parser.py
- api.py

### 2) Functions and classes used
- src/metrics.py: Metrics, record_rule(), summary()
- src/parser.py: Parser.consume(), Parser.parse_* methods
- api.py: token_type_summary(), parse_tree_node_counts(), _run_analysis_cached()

### 3) API routes connected
- POST /analyze
- POST /validate-syntax (partial metrics for token_count)

### 4) Data flow
Frontend input
-> POST /analyze
-> parser builds metrics in Metrics instance
-> Metrics.summary() returns dict
-> api.py adds computed counts and returns

### 5) Step-by-step execution flow
1. Parser created with Metrics.
2. Parser.consume() increments token_count.
3. Each parse_* method calls Metrics.record_rule(rule_name, depth).
4. Metrics.summary() returns token_count, rule applications, max depth, node count.
5. api.py adds rule_breakdown, parse_tree_node_counts, token_type_count.

### 6) Input and output structure
Input: tokens list, parse rules.
Output (analyze response):
- token_count
- rule_count (total_rule_applications)
- max_depth
- node_count
- rule_breakdown
- parse_tree_node_counts
- phase_times
- peak_memory_kb

### 7) How frontend communicates with backend
- Frontend requests /analyze and renders metrics from response fields.

### 8) What logic is implemented
- Metrics.record_rule tracks rule count and recursion depth.
- token_count is incremented per consumed token.
- node_count equals number of rule entries.

### 9) How results are generated
- Parser updates Metrics during parse.
- api.py combines Metrics.summary with token_type_summary and parse_tree_node_counts.

### 10) Data structures used
- Metrics object with counters.
- rule_breakdown dict.

### 11) Algorithms used
- Simple counter increments and max tracking.

### 12) Time complexity
- O(n) in number of tokens and parse rule entries.

### 13) Dependencies/libraries used
- No external metrics libraries.

### 14) Why those libraries are used
- Manual tracking is enough and predictable for educational analysis.

### 15) Important code blocks (what they do)
- Metrics.record_rule(): increments rule count, updates max depth, increments node_count.
- Parser.consume(): increments token_count.
- api.py parse_tree_node_counts(): computes internal/leaf counts.


## 5) COST CALCULATION (Frontend: Cost tab)

### 1) Backend files involved
- src/cost.py
- src/config.py
- api.py

### 2) Functions and classes used
- src/cost.py: compute_cost(), cost_breakdown(), _normalize_metric()
- src/config.py: ConfigManager.get_weight(), get_normalization()
- api.py: _run_analysis_cached() calls compute_cost and cost_breakdown

### 3) API routes connected
- POST /analyze

### 4) Data flow
Frontend input
-> POST /analyze
-> Metrics.summary() + timing + memory
-> compute_cost(metrics, total_ms, peak_memory_kb)
-> cost_breakdown(metrics, total_ms, peak_memory_kb)
-> response includes cost_score and cost_breakdown

### 5) Step-by-step execution flow
1. api.py measures total time and memory with perf_counter and tracemalloc.
2. metrics_summary is produced by parser.
3. compute_cost normalizes metrics and applies weights.
4. cost_breakdown calculates contributions and percentage shares.
5. cost_score and cost_breakdown are returned.

### 6) Input and output structure
Input: metrics_summary + total_ms + peak_memory_kb.
Output:
- cost_score: float (0-100)
- cost_breakdown: dict with raw_values, normalized_values, weights, contributions, total

### 7) How frontend communicates with backend
- Frontend renders cost values from /analyze response fields.

### 8) What logic is implemented
- Normalization: value / max_value (capped to 1.0).
- Weighted sum for token, depth, rules, time, memory.
- Converted to 0-100 scale.

### 9) How results are generated
- Weights and max values come from src/config.py (DEFAULT_CONFIG or config.json).
- cost_breakdown computes percentage contribution of each metric.

### 10) Data structures used
- Dicts for raw_values, normalized_values, weights, contributions.

### 11) Algorithms used
- Weighted sum and normalization (simple math).

### 12) Time complexity
- O(1) per request for cost calculation.

### 13) Dependencies/libraries used
- No external libraries; uses config manager only.

### 14) Why those libraries are used
- config.py allows centralized tuning of weights and thresholds.

### 15) Important code blocks (what they do)
- compute_cost(): loads weights and max values, normalizes, sums, scales to 100.
- cost_breakdown(): calculates raw values and contribution percentages.


## 6) AI SUGGESTIONS (Frontend: Suggestions tab)

### 1) Backend files involved
- api.py
- src/semantic.py (used in AI validation step)
- src/grammars/* (used to validate optimized code)

### 2) Functions and classes used
- api.py: generate_ai_suggestions(), _extract_structured_ai_payload(), _validate_ai_payload()
- api.py: _optimize_basic_code(), _simplify_expression_text()
- api.py: _validate_optimized_code()
- api.py: ai_suggestions() route
- huggingface_hub.InferenceClient

### 3) API routes connected
- POST /ai-suggestions

### 4) Data flow
Frontend input
-> POST /ai-suggestions (code, tokens, parse_tree_summary, cost, metrics)
-> generate_ai_suggestions() builds prompt and calls Hugging Face router
-> response parsed into issues/optimizations/optimized_code/explanation
-> optional deterministic fallback optimization
-> optional validation of optimized code
-> response returned to frontend

### 5) Step-by-step execution flow
1. Frontend calls /ai-suggestions after /analyze.
2. api.py builds payload and caches by JSON key.
3. generate_ai_suggestions() selects model candidates.
4. Hugging Face InferenceClient sends chat request.
5. Response text is parsed by _extract_structured_ai_payload().
6. If structured parsing is weak, fallback bullet extraction is applied.
7. Deterministic local optimizer (_optimize_basic_code) can override if model did not change code.
8. _validate_optimized_code() re-runs tokenize/parse/semantic on optimized code.
9. If validation fails, optimized_code is cleared and issue message added.
10. ai_processing_ms added and returned.

### 6) Input and output structure
Input to /ai-suggestions:
- code (string)
- tokens (list of token dicts)
- parse_tree_summary (string)
- cost (dict)
- metrics (dict)

Output:
- ai_suggestions: {issues, optimizations, optimized_code, explanation, ai_processing_ms}

### 7) How frontend communicates with backend
- Frontend posts JSON payload to /ai-suggestions and renders fields in Suggestions tab.

### 8) What logic is implemented
- Hugging Face router model calls for AI suggestions.
- Strict prompt with rules for compiler-style optimization.
- Post-processing that filters noise and ensures required fields.
- Deterministic local optimizer for algebraic simplifications.
- Validation of optimized code using existing lexer/parser/semantic analyzer.

### 9) How results are generated
- AI response is parsed into sections (ISSUES, OPTIMIZATIONS, OPTIMIZED CODE, EXPLANATION).
- If missing, fallback parsing is used.
- Deterministic local rules simplify algebra if AI does not change code.

### 10) Data structures used
- Plain dict payloads.
- JSON serialization for caching.
- Lists of bullet points for issues and optimizations.

### 11) Algorithms used
- Prompt-driven LLM generation.
- Regex-based response parsing and filtering.
- Local rewrite passes for algebraic simplification.

### 12) Time complexity
- Dominated by external model call.
- Local parsing and validation are O(n) in code size.

### 13) Dependencies/libraries used
- huggingface_hub.InferenceClient (model inference).
- urllib.request (model discovery on HF router).
- asyncio.to_thread (run cached sync function without blocking).
- Python re module for parsing and cleanup.

### 14) Why those libraries are used
- InferenceClient is the official Hugging Face client for hosted models.
- urllib.request fetches the router model list.
- asyncio keeps FastAPI endpoint responsive.

### 15) Important code blocks (what they do)
- generate_ai_suggestions(): builds prompt, selects models, makes API call.
- _extract_structured_ai_payload(): extracts sections by labels.
- _optimize_basic_code(): local simplifier for assignments with expressions.
- _validate_optimized_code(): re-tokenize, re-parse, and run SemanticAnalyzer.


## Module-by-module flow diagram (actual code path)

Tokenization:
Frontend action -> POST /analyze -> api.py analyze() -> _run_analysis_cached() -> grammar.tokenize() -> lexer.tokenize() / c_tokenize() / regex_tokenize() -> token dicts -> response -> frontend renders tokens

Parse Tree:
Frontend action -> POST /analyze -> api.py _run_analysis_cached() -> grammar.parse_with_metrics(tokens) -> Parser.parse() builds TreeNode -> api.py tree_to_dict() -> parse_tree JSON -> frontend renders tree

Semantic Analysis:
Frontend action -> POST /analyze -> api.py _run_analysis_cached() -> SemanticAnalyzer.analyze() -> semantic_analysis dict -> frontend renders errors/warnings/symbols

Metrics:
Frontend action -> POST /analyze -> Parser.consume()/Metrics.record_rule() -> Metrics.summary() -> api.py token_type_summary(), parse_tree_node_counts() -> response -> frontend renders charts and tables

Cost Calculation:
Frontend action -> POST /analyze -> compute_cost() + cost_breakdown() with config weights -> response -> frontend renders cost score and breakdown

AI Suggestions:
Frontend action -> POST /ai-suggestions -> generate_ai_suggestions() -> Hugging Face model -> parse/clean/validate -> response -> frontend renders issues/optimizations/explanation/optimized_code


## Dependencies and libraries by module

Tokenization:
- re (regex), manual tokenization
- No external lexer libs

Parse Tree:
- No external parser libs, manual recursive descent

Semantic Analysis:
- re for pattern matching

Metrics:
- No external libs

Cost Calculation:
- No external libs; uses src/config.py

AI Suggestions:
- huggingface_hub.InferenceClient
- urllib.request
- asyncio
- re


## Final summary for viva

Overall backend architecture summary:
- FastAPI orchestrates a manual compiler pipeline: tokenize -> parse -> semantic -> metrics -> cost -> suggestions. The core logic is implemented in small Python modules with minimal dependencies.

Most important backend files:
- api.py, src/lexer.py, src/parser.py, src/metrics.py, src/cost.py, src/semantic.py, src/advisor.py, src/grammars/__init__.py

Most complex modules:
- api.py (orchestration + AI parsing + caching)
- src/parser.py (recursive descent)
- api.py generate_ai_suggestions() (prompting, fallback, validation)

Tightly coupled parts:
- Parser and Metrics (Metrics.record_rule and consume are called in parser flow)
- api.py and grammars (api.py resolves grammar and uses grammar.tokenize/parse)
- cost/advisor depend on Metrics.summary format

Scalable parts:
- Grammar plugin system (src/grammars/__init__.py) allows new grammars.
- cost/advisor are configuration-driven via src/config.py.

Prototype-level parts:
- Semantic analysis is lightweight and regex-based (no full type system or scopes).
- AI suggestions depend on external service availability and response format.

Parts to improve:
- Semantic analysis: add scopes, types, and control-flow checks.
- Parser: better error recovery (currently raises SyntaxError on first issue).
- Tokenization: improve error reporting with spans and context.
- AI suggestions: add deterministic unit tests for parsing and validation.

Best viva explanation points:
- Manual recursive descent parser: easy to explain and trace.
- Metrics are collected inside the parser for accurate counts.
- Cost is normalized and weighted using config.json defaults.
- Semantic analysis is intentionally lightweight and educational.
- AI suggestions include strict prompt rules and validation by re-parsing.
