# Phase-Wise Compiler Cost Analyzer

A full-stack teaching and diagnostics tool that analyzes a tiny expression language through compiler phases:

1. Lexical analysis
2. Syntax parsing (recursive descent)
3. Metrics collection
4. Cost scoring
5. Refactoring suggestions
6. Interactive visualization

## Features

- FastAPI backend with typed request/response models
- Analysis modes: `tokens`, `syntax`, `full`
- Parse tree serialization for frontend rendering
- Cost score + component breakdown
- Rule-based refactoring advisor with hotspot warnings
- Syntax validation endpoint with line/column diagnostics
- Request-level caching for repeated analyses
- React + Vite frontend with:
  - Monaco editor + sample programs
  - Phase timeline
  - Parse tree explorer
  - Metrics charts (tokens, rules, cost terms)
  - Saved history + compare mode
  - Export report as JSON/Markdown

## Project Structure

- `src/` core compiler modules (`lexer.py`, `parser.py`, `metrics.py`, `cost.py`, `advisor.py`)
- `api.py` FastAPI service wrapper
- `main.py` CLI pipeline runner
- `frontend/` React dashboard
- `tests/` unit + API tests

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

- Ensure `frontend/vite.config.js` includes:
  - `'/ai-suggestions': 'http://localhost:8000'`
- Restart the Vite dev server after proxy changes (`npm run dev`), because proxy config is only loaded on startup.
- Confirm backend is running on port `8000` and OpenAPI docs list `POST /ai-suggestions` at `http://localhost:8000/docs`.

## API Usage

### POST `/analyze`

Request body:

```json
{
  "code": "x = 3 + 4; print(x);",
  "analysis_level": "full",
  "visualization": true
}
```

Notes:

- `code` and `source_code` are both accepted; either one is required.
- `analysis_level` options:
  - `tokens`: lexical only
  - `syntax`: lexical + parsing + metrics
  - `full`: all phases including cost + suggestions

### POST `/validate-syntax`

Returns syntax validity and token count or a 422 with line/column detail.

### GET `/stats`

Returns usage counters and cache statistics.

### GET `/health`

Basic liveness probe.

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

## Frontend Production Build

```bash
cd frontend
npm run build
```

## Docker

Build and run backend + frontend:

```bash
docker compose up --build
```

- Frontend: `http://localhost:5173`
- API: `http://localhost:8000`

## Deployment (Simple Option)

1. Build frontend static assets (`npm run build`)
2. Deploy backend container to your host/cloud
3. Serve frontend build via Nginx (or Vercel/Netlify) and point API base URL to backend
4. Enable CORS for your frontend origin in production
