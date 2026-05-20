# Phase-Wise Compiler Cost Analyzer

An educational, full-stack compiler analysis and visualization system for a small expression language. The tool makes parsing effort visible by exposing tokens, parse trees, structural metrics, and a heuristic cost score, then overlays rule-based refactoring suggestions. It is designed for teaching, demos, and explainability rather than production compilation.

## Quick Summary

- Pipeline phases: lexing, parsing, semantic analysis, metrics, cost, suggestions, visualization
- Back end: FastAPI service for analysis, semantic diagnostics, history, diff, and comparison reports
- Front end: React dashboard with a phase timeline, Monaco editor, charts, semantic diagnostics, and comparison views
- CLI runner: generates artifacts (parse tree DOT/PNG, metrics charts, comparison exports) for offline use

## What This Project Solves

Traditional compiler coursework tools mostly answer “accept or reject.” This project adds measurable visibility into parsing effort, semantic quality, and structural complexity for a small language by:

- Counting rule applications and parse depth
- Surfacing parse tree shape and node counts
- Detecting undeclared variables, duplicate assignments, and semantic anomalies
- Scoring complexity with a transparent, heuristic model
- Generating rule-based refactoring suggestions
- Comparing metric deltas, parse-tree diffs, and cost/performance tradeoffs across source variants

## Language Scope

The current grammar focuses on a tiny expression language with identifiers, numbers, assignment, print, arithmetic operators, parentheses, and semicolons. The project now includes lightweight semantic analysis for educational validation, while still not implementing a full type system, optimization engine, or target code generation.

## Implemented Features

### Core Compiler Pipeline

- Regex-based lexer with token location metadata
- Recursive descent parser that builds a parse tree
- Metrics collection during parsing (not post-processed)
- Heuristic cost model with term-level breakdown
- Rule-based advisor for suggestions and hotspots

### Backend API

- Typed request/response models
- Analysis modes: `tokens`, `syntax`, `full`
- Grammar registry and rules listing
- Semantic analysis output with symbol-table diagnostics, undeclared-variable errors, and duplicate-assignment warnings
- Parse-tree structural diff between two programs
- Compare endpoint for side-by-side cost, metric, and semantic analysis summaries
- Syntax validation with line/column diagnostics
- Request-level caching for repeated analyses
- Usage and history persistence to disk

### Frontend Dashboard

- Monaco editor with syntax, hotspot markers, and semantic diagnostics
- Phase timeline navigation
- Parse tree explorer with pan/zoom and node details
- Metrics, cost contribution, and semantic performance charts
- Comparison mode with side-by-side metric charts, cost breakdown comparisons, and parse-tree diff summaries
- Saved history with replay, selection-based comparison, and exportable comparison reports
- Export analysis as JSON/Markdown

### CLI Runner

- Runs the full pipeline over a file
- Outputs DOT and PNG parse tree artifacts
- Generates a metrics chart image

## Architecture Overview

### Backend Entry Points

- [api.py](api.py) — FastAPI service, caching, timing, grammar routing, history/usage persistence
- [main.py](main.py) — CLI pipeline runner and artifact output

### Compiler Core

- [src/lexer.py](src/lexer.py) — tokenization and token location metadata
- [src/parser.py](src/parser.py) — recursive descent parsing with location-aware errors
- [src/metrics.py](src/metrics.py) — metric aggregation and rule counts
- [src/cost.py](src/cost.py) — weighted cost computation and breakdown
- [src/semantic.py](src/semantic.py) — lightweight semantic analysis and symbol table diagnostics
- [src/advisor.py](src/advisor.py) — rule-based suggestions
- [src/tree.py](src/tree.py) — parse tree node model
- [src/visualizer.py](src/visualizer.py) — DOT/PNG parse tree and chart generation

### Grammar Plugin Layer

- [src/grammars/base.py](src/grammars/base.py) — grammar interface and metadata
- [src/grammars/default.py](src/grammars/default.py) — default grammar
- [src/grammars/__init__.py](src/grammars/__init__.py) — grammar registry and helpers

### Frontend Shell

- [frontend/src/App.jsx](frontend/src/App.jsx) — global UI state, history hydration, compare orchestration
- [frontend/src/main.jsx](frontend/src/main.jsx) — React bootstrap
- [frontend/src/index.css](frontend/src/index.css) — global styles and theme adjustments

### Frontend Components

- [frontend/src/components/InputPanel.jsx](frontend/src/components/InputPanel.jsx) — Monaco editor, grammar selection, markers, replay injection
- [frontend/src/components/StepController.jsx](frontend/src/components/StepController.jsx) — phase timeline, replay flow, export
- [frontend/src/components/ParseTreeView.jsx](frontend/src/components/ParseTreeView.jsx) — interactive parse tree
- [frontend/src/components/MetricsView.jsx](frontend/src/components/MetricsView.jsx) — metrics charts and cost breakdown
- [frontend/src/components/TokensView.jsx](frontend/src/components/TokensView.jsx) — token list and summaries
- [frontend/src/components/SuggestionView.jsx](frontend/src/components/SuggestionView.jsx) — suggestion cards
- [frontend/src/components/Sidebar.jsx](frontend/src/components/Sidebar.jsx) — complexity classification, timing, history
- [frontend/src/components/HistoryPanel.jsx](frontend/src/components/HistoryPanel.jsx) — replay and compare selection
- [frontend/src/components/ComparisonView.jsx](frontend/src/components/ComparisonView.jsx) — metric deltas and parse-tree diff summary

## Persistence and Outputs

- Backend stores usage counters, event logs, and analysis history in [output/](output/)
- CLI writes parse tree and chart artifacts into [output/](output/)

## Metrics and Cost Model

### Metrics Recorded

- Token count
- Total rule applications
- Maximum recursion depth
- Parse tree node count
- Per-rule breakdown

### Cost Formula

The heuristic model is a weighted linear score:

$$
	ext{Cost} = 0.5 \cdot \text{TokenCount} + 1.0 \cdot \text{RuleApplications} + 2.0 \cdot \text{MaxDepth} + 0.8 \cdot \text{ParseTreeNodes}
$$

Notes:

- The score is relative and dimensionless.
- It is not normalized to a fixed range.
- It is intended for within-project comparisons.

## Hotspot and Suggestion Rules

Advisor logic is deterministic and threshold-based. It flags:

- Deep nesting and recursion hotspots
- High operator density
- High token/rule/node counts and overall cost

These results are surfaced in the UI with severity mapping and in the API response.

## API Reference (Current)

### GET /health

Basic liveness probe.

### GET /grammars

List registered grammars and metadata.

### GET /grammar-rules

Return grammar rules for a selected grammar key.

### POST /validate-syntax

Validate syntax and return token count, or a 422 with line/column details.

### POST /analyze

Request body:

```json
{
  "code": "x = 3 + 4; print(x);",
  "analysis_level": "full",
  "visualization": true,
  "grammar": "default"
}
```

Notes:

- `code` and `source_code` are both accepted; either one is required.
- `analysis_level` values:
  - `tokens`: lexical only
  - `syntax`: lexical + parsing + metrics
  - `full`: all phases including cost + suggestions

### POST /parse-tree-diff

Structural diff between two programs. Accepts `source_a`/`source_b` or `code_a`/`code_b` with an optional `grammar` and `visualization` flag.

### POST /compare

Compare two or more analysis runs by returning paired metric summaries, cost deltas, semantic diagnostics, and optional parse-tree diff summaries.

### GET /stats

Usage counters and cache statistics.

### GET /history

Persisted analysis history rows.

## Setup

### Backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Run API:

```bash
uvicorn api:app --reload --port 8000
```

Run CLI:

```bash
python main.py input.txt
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend proxies API calls to `http://localhost:8000`.

### AI Suggestions Setup

AI suggestions require an API key in the backend environment. Set one of:

- `HF_API_KEY` (preferred)
- `GOOGLE_API_KEY`
- `GEMINI_API_KEY`

If you copied `.env` from the repo, update the key name from `GOOGLE_API_KEY` to `HF_API_KEY` when using a Hugging Face API token.

### Dev Proxy Troubleshooting

If the Suggestions tab shows `Request failed with status code 404` for AI output, the usual cause is a missing Vite proxy entry for `/ai-suggestions`.

- Ensure [frontend/vite.config.js](frontend/vite.config.js) includes a proxy entry for `/ai-suggestions` to `http://localhost:8000`.
- Restart the Vite dev server after proxy changes because proxy config loads on startup.
- Confirm the backend is running on port `8000` and OpenAPI docs list `POST /ai-suggestions` at `http://localhost:8000/docs`.

## Sample Input

```txt
x = 3 + 4 * 2;
y = x + 1;
print(y);
```

## Testing

```bash
pytest -q
```

## Docker

Build and run backend + frontend:

```bash
docker compose up --build
```

- Frontend: `http://localhost:5173`
- API: `http://localhost:8000`

## Deployment (Simple Option)

1. Build frontend static assets (`npm run build`).
2. Deploy the backend container to your host/cloud.
3. Serve the frontend build via Nginx (or Vercel/Netlify) and point the API base URL to the backend.
4. Enable CORS for your frontend origin in production.

## Limitations

- Grammar is intentionally small (assignments, arithmetic expressions, print).
- Semantic analysis is lightweight and educational; it is not a full type checker or complete semantic engine.
- Cost score weights are heuristic and not empirically calibrated.
- Error recovery is not implemented; parsing stops on the first syntax error.
- Graphviz PNG generation depends on external `dot` installation.

## Future Enhancements (Not Yet Implemented)

- Full semantic type inference and richer symbol-table validation
- Richer grammar with control flow, boolean expressions, and function calls
- Error recovery with multi-error reporting and incremental parsing
- Empirical calibration or normalization of cost weights
- Trend analysis and dataset-level comparison across multiple programs

## Key Files and Directories

- [src/](src/) — compiler core modules
- [api.py](api.py) — FastAPI backend and endpoints
- [main.py](main.py) — CLI pipeline runner
- [frontend/](frontend/) — React dashboard
- [tests/](tests/) — unit and API tests
- [docker-compose.yml](docker-compose.yml) — multi-container orchestration
- [requirements.txt](requirements.txt) — backend dependencies
- [pyproject.toml](pyproject.toml) — Python project metadata and pytest config
- [PROJECT_FULL_DOCUMENTATION.md](PROJECT_FULL_DOCUMENTATION.md) — extended background and methodology
- [PROJECT_STATUS_REPORT.md](PROJECT_STATUS_REPORT.md) — implementation status summary
