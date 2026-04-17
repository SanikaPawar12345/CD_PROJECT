# Project Status Report

## Overview
This repository implements a full-stack compiler phase analyzer with a backend API, a CLI runner, and a React/Vite frontend dashboard. The main focus is on analyzing a small expression language through compiler phases and producing metrics, cost scoring, parse tree visualization, and refactoring recommendations.

## Completed Components

### Backend
- FastAPI-based service in `api.py`
- Fully implemented request/response models using Pydantic
- Supported endpoints:
  - `GET /health`
  - `GET /grammars`
  - `GET /grammar-rules`
  - `GET /stats`
  - `GET /history`
  - `POST /validate-syntax`
  - `POST /analyze`
  - `POST /parse-tree-diff`
- Local usage logging and history persisted in `output/`
- CORS allowed for local development
- Analysis caching enabled with `functools.lru_cache`
- Hotspot detection and parse tree diff support included

### CLI Runner
- `main.py` executes the full compiler pipeline on a source file
- Pipeline phases:
  1. Lexical analysis
  2. Syntax parsing
  3. Metrics collection
  4. Cost scoring
  5. Refactoring suggestions
  6. Visualization output
- Generates output files in `output/`:
  - `parse_tree.dot`
  - `parse_tree.png`
  - `metrics_chart.png`
- Accepts an input file path argument and prints phase summaries

### Core Compiler Logic
- Core modules located in `src/`
- Implemented features:
  - `lexer.py` for tokenization
  - `parser.py` for recursive descent parsing
  - `metrics.py` for parse metrics and rule counts
  - `cost.py` for weighted cost scoring and breakdowns
  - `advisor.py` for refactoring suggestions
  - `visualizer.py` for parse tree and metrics chart generation
- Grammar system available under `src/grammars/`
  - `default.py` grammar loaded by API
  - `base.py` containing shared grammar utilities

### Frontend
- React + Vite single-page app in `frontend/`
- Uses Monaco editor integration and chart visualization
- Supports interactive analysis, history, parse tree rendering, and comparison views
- Frontend dependencies and scripts in `frontend/package.json`
- Completed basic run workflow:
  - `npm install`
  - `npm run dev`

### Docker Support
- `Dockerfile` for backend containerization
- `frontend/Dockerfile` for frontend build/runtime
- `docker-compose.yml` to build and run both services together

### Testing
- `pytest` configuration in `pyproject.toml`
- Tests available in `tests/`
  - `test_api.py`
  - `test_lexer.py`
  - `test_metrics_cost_advisor.py`
  - `test_parser.py`
- Simple `pytest -q` command supported

## Dependencies

### Backend
- `fastapi>=0.110.0`
- `uvicorn[standard]>=0.29.0`
- `python-multipart>=0.0.9`
- `graphviz>=0.20`
- `matplotlib>=3.7`

### Frontend
- `react` `^18.2.0`
- `react-dom` `^18.2.0`
- `@monaco-editor/react` `^4.7.0`
- `axios` `^1.6.7`
- `chart.js` `^4.4.2`
- `react-chartjs-2` `^5.2.0`
- `framer-motion` `^11.0.8`
- `vite` and Tailwind toolchain

## Current Project Status
- Backend API is fully defined and operational for local development.
- CLI analysis flow is complete and provides phase-by-phase output plus export files.
- Frontend application is scaffolded and ready to run with the established development workflow.
- Docker compose integration is available for end-to-end launch of backend and frontend together.
- Testing harness exists and is configured with `pytest`.

## Usage Summary

### Run backend
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn api:app --reload --port 8000
```

### Run frontend
```powershell
cd frontend
npm install
npm run dev
```

### Run CLI
```powershell
python main.py input.txt
```

### Run Docker
```powershell
docker compose up --build
```

### Run tests
```powershell
pytest -q
```

## Notes
- The project is structured for teaching compiler phases and interactive diagnostics.
- The API logs usage and history to `output/` for later review.
- Frontend and backend communicate through `http://localhost:8000` in development mode.

## Files of Interest
- `README.md` — project overview and setup instructions
- `api.py` — FastAPI backend and endpoints
- `main.py` — CLI pipeline runner
- `pyproject.toml` — Python project metadata and dependencies
- `frontend/package.json` — frontend scripts and dependencies
- `docker-compose.yml` — multi-container orchestration
- `src/` — compiler implementation modules
- `tests/` — validation test cases
