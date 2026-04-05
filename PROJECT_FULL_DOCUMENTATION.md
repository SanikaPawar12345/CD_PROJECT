# Phase-Wise Compiler Cost Analyzer

## 1. Project Identity

This is a full-stack compiler analysis and visualization system for a small expression language.

It combines:

- Python compiler core (lexer, parser, metrics, cost, advisor)
- FastAPI service layer for analysis APIs
- React dashboard for step-by-step visualization
- Compare mode for multi-run analysis and structural diffing

The project is designed for academic demo, explainability, and practical code-structure feedback.

## 2. What The Project Is Used For

### 2.1 Single-run analysis

Given source code, the app shows:

- tokenization output
- parse tree graph
- grammar rule metrics
- cost score and contributions
- suggestions and hotspots

### 2.2 Syntax pre-check

Before full analysis, syntax can be validated quickly with location-aware errors.

### 2.3 Multi-run comparison

Users can compare 2 or more saved runs and inspect:

- metric deltas vs baseline
- parse-tree structural differences

### 2.4 Replay of historical analyses

Saved analyses can be replayed with the same phase-by-phase animation flow.

### 2.5 Persistent historical and usage insights

History and usage logs persist to backend files for continuity across sessions.

## 3. Compiler Pipeline And UI Mapping

Backend logic still follows the same core compiler phases, but UI now exposes six presentation steps:

1. Input
2. Tokenization
3. Parsing
4. Metrics
5. Cost
6. Suggestions

Why this mapping:

- keeps educational clarity
- separates complexity metrics from cost interpretation
- gives a clean progression for demo and replay

## 4. Technology Choices And Reasons

### Python + FastAPI

Chosen because:

- compiler logic already exists in Python
- FastAPI supports strong typed contracts
- easy endpoint testing with pytest and TestClient

### React + Vite + Tailwind

Chosen because:

- modular, fast iteration for UX-heavy dashboard
- utility styling keeps visual consistency
- good fit for stateful phase/timeline interactions

### Framer Motion

Used for smooth phase and panel transitions.

### Monaco Editor

Used for source editing with diagnostics markers (syntax + hotspot highlighting).

### Chart.js

Used for metrics and cost contribution visualizations.

## 5. Current Feature Set (Implemented)

### 5.1 Rich API analysis contract

`/analyze` supports:

- `analysis_level`: tokens | syntax | full
- `visualization` toggle
- `grammar` selection

Returns extended fields:

- token summaries
- rule breakdown
- parse tree
- cost breakdown
- hotspots
- `analysis_id`
- `phase_times` (lexical/parsing/total)

### 5.2 Better diagnostics

- lexer and parser report line/column
- frontend maps these into Monaco markers

### 5.3 Compare mode improvements

- input remains visible
- comparison renders in dedicated section
- metric deltas shown with explicit direction:
  - `+N ↑` (increase)
  - `-N ↓` (decrease)

### 5.4 Parse tree graph (interactive)

SVG parse tree now supports:

- pan/zoom/reset
- clickable nodes
- selected-node details:
  - node type
  - depth
  - child count

### 5.5 Parse-tree diff mode

Backend and UI support structural diffs:

- added/removed/changed nodes
- total node counts (A/B)
- sample changed paths

### 5.6 Replay analysis

History panel includes `Replay Analysis` action.

Replay behavior:

- reloads source in editor
- replays phases sequentially
- restores previously captured analysis payload

### 5.7 Grammar plugin architecture

Introduced grammar registry with pluggable implementations.

Currently available:

- `default`
- `strict-v1`

Added grammar rules endpoint and UI panel to view rules.

### 5.8 Cost breakdown panel

Cost now has contribution bars/percentages for:

- token term
- rule term
- depth term
- node term

### 5.9 Complexity classification

Cost score classification in sidebar:

- Low (green)
- Moderate (orange)
- High (red)

### 5.10 Phase execution time visibility

Sidebar shows:

- lexical analysis time
- parsing time
- total analysis time

Timing is informational only and not used in cost formula.

### 5.11 Hotspot improvements

Hotspot detection includes:

- nested-expression/deep-recursion
- high operator density

Monaco markers use severity mapping:

- deep nesting => red
- operator density => orange/warning

### 5.12 Persistent usage/history logging

Backend persists:

- usage counters
- event log stream
- analysis history rows with payload snapshots

### 5.13 Timeline-only phase navigation

The top timeline now acts as the single navigation control for phase views.

- duplicate lower tab navigation removed
- clicking timeline steps opens corresponding phase panel

### 5.14 Independent pane scrolling

Left sidebar and right main content now scroll independently so saved history remains accessible while browsing content.

## 6. File Responsibility Map

### 6.1 Backend entry points

- [main.py](main.py)
  - CLI pipeline runner and output generation

- [api.py](api.py)
  - FastAPI endpoints
  - caching
  - timing collection
  - grammar routing
  - parse-tree diff
  - usage/history persistence

### 6.2 Compiler core

- [src/lexer.py](src/lexer.py)
  - tokenization and token location metadata

- [src/parser.py](src/parser.py)
  - recursive descent parsing with location-aware errors

- [src/metrics.py](src/metrics.py)
  - metric aggregation

- [src/cost.py](src/cost.py)
  - weighted cost computation and breakdown

- [src/advisor.py](src/advisor.py)
  - rule-based structural suggestions

- [src/tree.py](src/tree.py)
  - parse tree node model

- [src/visualizer.py](src/visualizer.py)
  - CLI visual artifact rendering

### 6.3 Grammar plugin layer

- [src/grammars/base.py](src/grammars/base.py)
  - plugin interface + metadata shape

- [src/grammars/default.py](src/grammars/default.py)
  - default grammar definitions and rules

- [src/grammars/__init__.py](src/grammars/__init__.py)
  - registry + lookup + list API helpers

### 6.4 Frontend shell

- [frontend/src/App.jsx](frontend/src/App.jsx)
  - global UI state
  - compare mode orchestration
  - backend hydration for history/stats
  - split-pane scrolling layout

- [frontend/src/main.jsx](frontend/src/main.jsx)
  - React app bootstrap

- [frontend/src/index.css](frontend/src/index.css)
  - global styles, theme adjustments, visual consistency helpers

### 6.5 Frontend components

- [frontend/src/components/InputPanel.jsx](frontend/src/components/InputPanel.jsx)
  - Monaco editor
  - grammar selector
  - hotspot/syntax markers
  - external code injection for replay

- [frontend/src/components/StepController.jsx](frontend/src/components/StepController.jsx)
  - full phase workflow orchestration
  - timeline navigation
  - replay sequencing
  - grammar rules panel
  - report export

- [frontend/src/components/ParseTreeView.jsx](frontend/src/components/ParseTreeView.jsx)
  - interactive parse tree graph with node details

- [frontend/src/components/MetricsView.jsx](frontend/src/components/MetricsView.jsx)
  - metrics charts + cost contribution panel

- [frontend/src/components/TokensView.jsx](frontend/src/components/TokensView.jsx)
  - token list + token summary tables

- [frontend/src/components/SuggestionView.jsx](frontend/src/components/SuggestionView.jsx)
  - suggestion cards

- [frontend/src/components/Sidebar.jsx](frontend/src/components/Sidebar.jsx)
  - snapshot cards
  - complexity classification
  - timing panel
  - usage insights
  - history host

- [frontend/src/components/HistoryPanel.jsx](frontend/src/components/HistoryPanel.jsx)
  - compare selection + replay action

- [frontend/src/components/ComparisonView.jsx](frontend/src/components/ComparisonView.jsx)
  - multi-run comparison + directional deltas + parse-tree diff summary

### 6.6 Build, config, and automation

- [requirements.txt](requirements.txt)
  - backend dependencies + test tools

- [pyproject.toml](pyproject.toml)
  - pytest configuration and project metadata

- [frontend/package.json](frontend/package.json)
  - frontend scripts and dependencies

- [frontend/vite.config.js](frontend/vite.config.js)
  - dev server and API proxying

- [Dockerfile](Dockerfile)
  - backend container

- [frontend/Dockerfile](frontend/Dockerfile)
  - frontend build/serve container

- [docker-compose.yml](docker-compose.yml)
  - local multi-service composition

- [.github/workflows/ci.yml](.github/workflows/ci.yml)
  - CI tests and frontend build

## 7. API Endpoint Reference (Current)

### GET /health

- liveness check

### GET /grammars

- list registered grammars and metadata

### GET /grammar-rules

- returns grammar rules for selected grammar key
- query: `grammar`

### POST /validate-syntax

- fast syntax validation
- inputs: `source_code` or `code`, `grammar`

### POST /analyze

- executes full/tokens/syntax analysis
- inputs:
  - `source_code` or `code`
  - `analysis_level`
  - `visualization`
  - `grammar`
- returns tokens, parse tree, metrics, cost, hotspots, suggestions, timings

### POST /parse-tree-diff

- structural diff between two source programs
- inputs:
  - `source_a`/`source_b` or `code_a`/`code_b`
  - `grammar`
  - `visualization`

### GET /stats

- usage and cache counters

### GET /history

- persisted historical analysis rows

## 8. Persistence Files

Created under [output](output):

- [output/usage_stats.json](output/usage_stats.json)
  - aggregate usage counters

- [output/usage_log.jsonl](output/usage_log.jsonl)
  - append-only event stream

- [output/analysis_history.jsonl](output/analysis_history.jsonl)
  - append-only historical analysis records (includes payload snapshots for replay)

## 9. Testing And Validation Status

### Automated coverage includes

- lexer behavior and location-aware errors
- parser correctness and error surfaces
- metrics/cost/advisor behavior
- API health/analyze/validate endpoints

Test files:

- [tests/test_lexer.py](tests/test_lexer.py)
- [tests/test_parser.py](tests/test_parser.py)
- [tests/test_metrics_cost_advisor.py](tests/test_metrics_cost_advisor.py)
- [tests/test_api.py](tests/test_api.py)

### Validation state

- backend tests passing
- frontend production build passing

## 10. Run Guide

### Backend (dev)

1. Create and activate venv
2. Install dependencies
3. Run API server

### Frontend (dev)

1. Install dependencies
2. Run Vite dev server

### CLI

- Run [main.py](main.py) with input file

### Docker

- Use compose if Docker is available locally

## 11. Why This Architecture Works

### Clear separation

- compiler logic in `src`
- transport/orchestration in API
- visualization and interaction in frontend

### Extensible by design

- grammar plugin model avoids hard-coding a single grammar implementation

### UX optimized for explanation

- timeline-based phase navigation
- replay support
- interactive parse graph
- compare + diff for structural reasoning

### Operationally traceable

- persistent usage and history logs

## 12. Current Boundaries

- grammar library still small (default + strict-v1)
- parse-tree diff is path-based structural diff (not semantic AST equivalence)
- frontend bundle remains relatively large because editor + chart stack is heavy

## 13. Next Relevant Improvements

- add grammar-specific semantic diff heuristics
- add lazy loading for heavy frontend modules
- add fine-grained replay controls (pause/resume/skip)
- add additional grammar plugins while preserving current API contracts

## 14. One-Paragraph Summary

This project is now a modular compiler visualization tool that supports end-to-end analysis, interactive parse-tree exploration, detailed cost interpretation, replayable historical runs, multi-run comparison with structural diffing, and persistent usage/history observability, while keeping the original architecture intact and extensible.
