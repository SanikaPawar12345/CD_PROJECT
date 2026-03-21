# api.py
# FastAPI wrapper for Phase-Wise Compiler Cost Analyzer
# Exposes existing compiler logic via HTTP endpoints.
# Does NOT modify any logic in src/.

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.lexer    import tokenize
from src.parser   import Parser
from src.cost     import compute_cost, cost_breakdown
from src.advisor  import get_suggestions

app = FastAPI(title="Phase-Wise Compiler Cost Analyzer API", version="1.0.0")

# Allow all origins for local dev; tighten for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
#  Request / Response schemas
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    source_code: str


# ---------------------------------------------------------------------------
#  Helper: recursively convert TreeNode → plain dict for JSON serialisation
# ---------------------------------------------------------------------------

def tree_to_dict(node) -> dict:
    """Convert a TreeNode object into a JSON-serialisable dict."""
    return {
        "type":     node.label,
        "terminal": node.is_leaf(),
        "children": [tree_to_dict(child) for child in node.children],
    }


# ---------------------------------------------------------------------------
#  Helper: count tokens by type (for the summary table in the frontend)
# ---------------------------------------------------------------------------

def token_type_summary(tokens: list) -> dict:
    """
    Returns a dict mapping each token type to its count.
    EOF is excluded.
    Example: {"ID": 2, "NUMBER": 3, "PLUS": 1, ...}
    """
    summary: dict[str, int] = {}
    for tok in tokens:
        if tok.type == "EOF":
            continue
        summary[tok.type] = summary.get(tok.type, 0) + 1
    return summary


# ---------------------------------------------------------------------------
#  Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health_check():
    """Simple liveness check."""
    return {"status": "ok", "message": "Compiler API is running."}


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    """
    Run the full compiler pipeline on the submitted source code.

    Returns:
        tokens          – list of {type, value} objects (no EOF)
        token_type_count– dict of token_type -> total count  (for summary table)
        token_count     – total token count (excl. EOF)
        rule_count      – total grammar rule applications
        max_depth       – maximum parse recursion depth
        node_count      – total parse tree nodes
        parse_tree      – nested {type, terminal, children} dict
        metrics         – full metrics summary dict
        cost_score      – weighted cost score (float)
        cost_breakdown  – per-term breakdown dict
        suggestions     – list of advisory strings
    """
    source = request.source_code.strip()
    if not source:
        raise HTTPException(status_code=400, detail="source_code must not be empty.")

    # Phase 1 – Lexical analysis
    try:
        tokens = tokenize(source)
    except SyntaxError as e:
        raise HTTPException(status_code=422, detail=f"Lexer error: {e}")

    # Phase 2 – Syntax analysis (parse tree + metrics)
    try:
        parser = Parser(tokens)
        tree   = parser.parse()
    except SyntaxError as e:
        raise HTTPException(status_code=422, detail=f"Parser error: {e}")

    # Phase 3 – Metrics
    metrics_summary = parser.metrics.summary()

    # Phase 4 – Cost
    cost_score = compute_cost(metrics_summary)
    breakdown  = cost_breakdown(metrics_summary)

    # Phase 5 – Suggestions
    suggestions = get_suggestions(metrics_summary, cost_score)

    # Serialise tokens (exclude EOF)
    token_list = [
        {"type": t.type, "value": t.value}
        for t in tokens
        if t.type != "EOF"
    ]

    return {
        "tokens":           token_list,
        "token_type_count": token_type_summary(tokens),   # <-- summary table data
        "token_count":      metrics_summary["token_count"],
        "rule_count":       metrics_summary["total_rule_applications"],
        "max_depth":        metrics_summary["max_recursion_depth"],
        "node_count":       metrics_summary["parse_tree_nodes"],
        "parse_tree":       tree_to_dict(tree),
        "metrics":          metrics_summary,
        "cost_score":       cost_score,
        "cost_breakdown":   breakdown,
        "suggestions":      suggestions,
    }
