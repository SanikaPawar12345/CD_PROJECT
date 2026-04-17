import sys
import os
import re
import json
import hashlib
import asyncio
import logging
from datetime import datetime, UTC
from functools import lru_cache
from time import perf_counter
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from huggingface_hub import InferenceClient
from huggingface_hub.errors import HfHubHTTPError
from pydantic import BaseModel
from dotenv import load_dotenv

# Load backend environment variables from project-root .env when available.
load_dotenv(Path(__file__).resolve().parent / ".env")

from src.cost import compute_cost, cost_breakdown
from src.advisor import get_suggestions
from src.grammars import get_grammar, list_grammars

app = FastAPI(title="Phase-Wise Compiler Cost Analyzer API", version="2.0.0")
LOGGER = logging.getLogger("compiler-ai")

LOG_DIR = Path("output")
LOG_DIR.mkdir(parents=True, exist_ok=True)
USAGE_STATS_FILE = LOG_DIR / "usage_stats.json"
USAGE_LOG_FILE = LOG_DIR / "usage_log.jsonl"
ANALYSIS_HISTORY_FILE = LOG_DIR / "analysis_history.jsonl"

USAGE_STATS_DEFAULTS = {
    "analyze_calls": 0,
    "syntax_validate_calls": 0,
    "parse_tree_diff_calls": 0,
    "ai_suggestion_calls": 0,
    "cache_hits": 0,
}


def _load_usage_stats() -> dict[str, int]:
    if not USAGE_STATS_FILE.exists():
        return dict(USAGE_STATS_DEFAULTS)
    try:
        loaded = json.loads(USAGE_STATS_FILE.read_text(encoding="utf-8"))
        merged = dict(USAGE_STATS_DEFAULTS)
        merged.update({k: int(v) for k, v in loaded.items() if isinstance(v, (int, float))})
        return merged
    except Exception:
        return dict(USAGE_STATS_DEFAULTS)


def _save_usage_stats() -> None:
    USAGE_STATS_FILE.write_text(json.dumps(USAGE_STATS, indent=2), encoding="utf-8")


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


USAGE_STATS = _load_usage_stats()

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
    code: str | None = None
    source_code: str | None = None
    analysis_level: Literal["tokens", "syntax", "full"] = "full"
    visualization: bool = True
    grammar: str = "default"


class AnalyzeResponse(BaseModel):
    analysis_id: str
    grammar: str
    tokens: list[dict[str, Any]]
    token_type_count: dict[str, int]
    token_count: int
    rule_count: int
    max_depth: int
    node_count: int
    parse_tree: dict[str, Any] | None
    parse_tree_summary: str
    parse_tree_node_counts: dict[str, int]
    metrics: dict[str, Any]
    rule_breakdown: dict[str, int]
    cost_score: float
    cost_breakdown: dict[str, float]
    suggestions: list[str]
    hotspots: list[dict[str, Any]]
    phase_times: dict[str, float]


class SyntaxValidateResponse(BaseModel):
    valid: bool
    token_count: int
    message: str
    grammar: str


class ParseTreeDiffRequest(BaseModel):
    source_a: str | None = None
    source_b: str | None = None
    code_a: str | None = None
    code_b: str | None = None
    grammar: str = "default"
    visualization: bool = True


class ParseTreeDiffResponse(BaseModel):
    grammar: str
    summary: dict[str, int]
    samples: dict[str, list[str]]
    tree_a: dict[str, Any] | None
    tree_b: dict[str, Any] | None


class AISuggestionRequest(BaseModel):
    code: str
    tokens: list[dict[str, Any]]
    parse_tree_summary: str
    cost: dict[str, Any]
    metrics: dict[str, Any]


class AISuggestionPayload(BaseModel):
    issues: list[str]
    optimizations: list[str]
    optimized_code: str
    explanation: str


class AISuggestionResponse(BaseModel):
    ai_suggestions: AISuggestionPayload


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


def flatten_tree_paths(node: dict[str, Any] | None, prefix: str = "0") -> dict[str, str]:
    if not node:
        return {}
    result = {prefix: node.get("type", "Node")}
    for index, child in enumerate(node.get("children", [])):
        child_prefix = f"{prefix}.{index}"
        result.update(flatten_tree_paths(child, child_prefix))
    return result


def diff_parse_trees(tree_a: dict[str, Any] | None, tree_b: dict[str, Any] | None) -> dict[str, Any]:
    paths_a = flatten_tree_paths(tree_a)
    paths_b = flatten_tree_paths(tree_b)

    keys_a = set(paths_a)
    keys_b = set(paths_b)

    added_paths = sorted(keys_b - keys_a)
    removed_paths = sorted(keys_a - keys_b)
    changed_paths = sorted(
        key for key in (keys_a & keys_b)
        if paths_a.get(key) != paths_b.get(key)
    )

    return {
        "summary": {
            "added": len(added_paths),
            "removed": len(removed_paths),
            "changed": len(changed_paths),
            "total_a": len(paths_a),
            "total_b": len(paths_b),
        },
        "samples": {
            "added": [f"{path}:{paths_b[path]}" for path in added_paths[:20]],
            "removed": [f"{path}:{paths_a[path]}" for path in removed_paths[:20]],
            "changed": [f"{path}:{paths_a[path]}->{paths_b[path]}" for path in changed_paths[:20]],
        },
    }


def parse_tree_node_counts(node: dict | None) -> dict[str, int]:
    counts = {"internal": 0, "leaf": 0, "total": 0}
    if not node:
        return counts

    stack = [node]
    while stack:
        current = stack.pop()
        counts["total"] += 1
        if current.get("terminal"):
            counts["leaf"] += 1
        else:
            counts["internal"] += 1
        stack.extend(current.get("children", []))
    return counts


def summarize_parse_tree(node: dict[str, Any] | None, max_depth: int = 5, max_children: int = 4) -> str:
    """Create a concise textual parse-tree summary for prompt-friendly AI context."""
    if not node:
        return "Parse tree unavailable."

    def render(current: dict[str, Any], depth: int) -> str:
        label = str(current.get("type", "Node"))
        children = current.get("children", [])
        if not children:
            return label
        if depth >= max_depth:
            return f"{label}(...)"

        rendered = [render(child, depth + 1) for child in children[:max_children]]
        if len(children) > max_children:
            rendered.append("...")
        return f"{label}({', '.join(rendered)})"

    root_label = str(node.get("type", "Node"))
    direct_children = [str(child.get("type", "Node")) for child in node.get("children", [])[:6]]
    if len(node.get("children", [])) > 6:
        direct_children.append("...")

    return "\n".join([
        f"Root: {root_label}",
        f"Children: {', '.join(direct_children) if direct_children else 'None'}",
        f"Structure: {render(node, 0)}",
    ])


def detect_hotspots(source: str, metrics_summary: dict) -> list[dict[str, Any]]:
    hotspots: list[dict[str, Any]] = []
    lines = source.splitlines() or [source]

    for idx, line in enumerate(lines, start=1):
        if len(line) > 80:
            hotspots.append({
                "line": idx,
                "column": 1,
                "severity": "medium",
                "kind": "long-line",
                "message": "Line is longer than 80 characters and may be hard to read.",
            })
        if line.count("(") >= 3:
            hotspots.append({
                "line": idx,
                "column": max(1, line.find("(") + 1),
                "severity": "high",
                "kind": "nested-expression",
                "message": "Multiple nested parentheses found; consider simplifying expression depth.",
            })

        operator_count = line.count('+') + line.count('*')
        if operator_count >= 4:
            first_plus = line.find('+')
            first_star = line.find('*')
            candidates = [pos for pos in [first_plus, first_star] if pos >= 0]
            first_operator = min(candidates) if candidates else 0
            hotspots.append({
                "line": idx,
                "column": first_operator + 1,
                "severity": "medium",
                "kind": "operator-density",
                "message": f"High operator density detected ({operator_count} operators on one line).",
            })

    if metrics_summary.get("max_recursion_depth", 0) >= 8:
        hotspots.append({
            "line": None,
            "column": None,
            "severity": "high",
            "kind": "deep-recursion",
            "message": "Parser recursion depth is high; expression structure likely too nested.",
        })

    return hotspots[:15]


def parse_line_column(message: str) -> dict[str, int | None]:
    match = re.search(r"line\s+(\d+),\s*column\s+(\d+)", message)
    if not match:
        return {"line": None, "column": None}
    return {"line": int(match.group(1)), "column": int(match.group(2))}


def resolve_source(request: AnalyzeRequest) -> str:
    source = (request.source_code or request.code or "").strip()
    if not source:
        raise HTTPException(status_code=400, detail={
            "message": "Provide either 'source_code' or 'code'.",
            "line": None,
            "column": None,
        })
    return source


def _coerce_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _validate_ai_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("AI model did not return a JSON object.")

    issues = _coerce_string_list(payload.get("issues", []))
    optimizations = _coerce_string_list(payload.get("optimizations", []))
    optimized_code = str(payload.get("optimized_code", "")).strip()
    explanation = str(payload.get("explanation", "")).strip()

    if not optimized_code:
        raise ValueError("AI response is missing 'optimized_code'.")
    if not explanation:
        raise ValueError("AI response is missing 'explanation'.")

    return {
        "issues": issues,
        "optimizations": optimizations,
        "optimized_code": optimized_code,
        "explanation": explanation,
    }


def _extract_bullet_points(text: str) -> list[str]:
    bullets: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"^(?:[-*]|\d+\.)\s+", "", line)
        if line:
            bullets.append(line)
    return bullets


def generate_ai_suggestions(
    code: str,
    tokens: list[dict[str, Any]],
    parse_tree_summary: str,
    cost: dict[str, Any],
    metrics: dict[str, Any],
) -> dict[str, Any]:
    fallback = {
        "issues": [],
        "optimizations": ["AI suggestions currently unavailable"],
        "optimized_code": code,
        "explanation": "AI suggestions currently unavailable",
    }

    api_key = (os.getenv("HF_API_KEY") or "").strip()
    if not api_key:
        LOGGER.error("AI fallback reason: HF_API_KEY is missing or empty.")
        return fallback
    model_name = (os.getenv("HF_MODEL") or "google/flan-t5-base").strip()
    LOGGER.info(
        "HF debug: key_present=%s key_prefix=%s model=%s",
        bool(api_key),
        api_key[:4],
        model_name,
    )

    metrics_readable = {
        "token_count": metrics.get("token_count"),
        "total_rule_applications": metrics.get("total_rule_applications"),
        "max_recursion_depth": metrics.get("max_recursion_depth"),
        "parse_tree_nodes": metrics.get("parse_tree_nodes"),
        "rule_breakdown": metrics.get("rule_breakdown", {}),
        "cost": cost,
        "token_preview": tokens[:25],
    }

    prompt = (
        "You are a senior compiler optimization assistant.\n"
        "This is output from a compiler analysis system.\n"
        "Analyze the code and provide practical improvements that preserve behavior.\n"
        "Focus on: simplification suggestions, readability improvements, and reducing nesting/complexity.\n"
        "Return concise bullet points only.\n\n"
        "Output format:\n"
        "- Issues:\n"
        "  - ...\n"
        "- Optimizations:\n"
        "  - ...\n"
        "- Explanation:\n"
        "  - ...\n\n"
        f"Code:\n{code}\n\n"
        f"Compiler metrics (readable):\n{json.dumps(metrics_readable, ensure_ascii=True, indent=2)}\n\n"
        f"Parse tree summary:\n{parse_tree_summary}\n"
    )

    try:
        client = InferenceClient(token=api_key)
    except Exception as error:
        LOGGER.exception("AI fallback reason: failed to initialize InferenceClient: %s", error)
        return fallback

    response_text = ""
    try:
        # Text-generation models expect a plain prompt argument.
        response_text = client.text_generation(
            prompt=prompt,
            model=model_name,
            max_new_tokens=512,
            temperature=0.2,
            do_sample=True,
            return_full_text=False,
        )
    except ValueError as error:
        if "Supported task: conversational" in str(error):
            LOGGER.warning(
                "text_generation unsupported for model=%s; retrying with chat.completions.create",
                model_name,
            )
            try:
                chat_response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a senior compiler optimization assistant.",
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    max_tokens=512,
                    temperature=0.2,
                )
                choices = getattr(chat_response, "choices", [])
                if choices:
                    message = getattr(choices[0], "message", None)
                    response_text = getattr(message, "content", "") or ""
            except HfHubHTTPError as chat_http_error:
                LOGGER.exception(
                    "AI fallback reason: Hugging Face HTTP error for model=%s status=%s error=%s",
                    model_name,
                    getattr(chat_http_error.response, "status_code", "unknown"),
                    chat_http_error,
                )
                return fallback
            except Exception as chat_error:
                LOGGER.exception(
                    "AI fallback reason: chat completion call failed for model=%s with error=%s",
                    model_name,
                    chat_error,
                )
                return fallback
        else:
            LOGGER.exception(
                "AI fallback reason: text_generation value error for model=%s: %s",
                model_name,
                error,
            )
            return fallback
    except HfHubHTTPError as error:
        LOGGER.exception(
            "AI fallback reason: Hugging Face HTTP error for model=%s status=%s error=%s",
            model_name,
            getattr(error.response, "status_code", "unknown"),
            error,
        )
        return fallback
    except StopIteration:
        LOGGER.exception(
            "AI fallback reason: no text-generation provider mapping found for model=%s. "
            "Set HF_MODEL to a router-supported model for your token.",
            model_name,
        )
        return fallback
    except Exception as error:
        LOGGER.exception(
            "AI fallback reason: text_generation call failed for model=%s with error=%s",
            model_name,
            error,
        )
        return fallback

    if not isinstance(response_text, str) or not response_text.strip():
        LOGGER.warning("AI fallback reason: Hugging Face API returned empty response text.")
        return fallback

    points = _extract_bullet_points(response_text)
    if not points:
        LOGGER.warning("AI fallback reason: response had no parseable bullet points. Preview=%s", response_text[:200])
        return fallback

    issues = points[:3]
    optimizations = points[3:9] if len(points) > 3 else points
    explanation = " ".join(points[:4]).strip()[:1200]

    payload = {
        "issues": issues,
        "optimizations": optimizations,
        "optimized_code": code,
        "explanation": explanation or "Suggestions generated from compiler analysis context.",
    }
    return _validate_ai_payload(payload)


@lru_cache(maxsize=128)
def _run_ai_suggestions_cached(payload_key: str) -> dict[str, Any]:
    payload = json.loads(payload_key)
    return generate_ai_suggestions(
        code=payload["code"],
        tokens=payload["tokens"],
        parse_tree_summary=payload["parse_tree_summary"],
        cost=payload["cost"],
        metrics=payload["metrics"],
    )


def resolve_grammar_or_400(grammar_key: str):
    try:
        return get_grammar(grammar_key)
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"message": str(error), "line": None, "column": None})


def resolve_diff_sources(request: ParseTreeDiffRequest) -> tuple[str, str]:
    source_a = (request.source_a or request.code_a or "").strip()
    source_b = (request.source_b or request.code_b or "").strip()
    if not source_a or not source_b:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Provide both source_a/source_b (or code_a/code_b).",
                "line": None,
                "column": None,
            },
        )
    return source_a, source_b


@lru_cache(maxsize=256)
def _run_analysis_cached(source: str, analysis_level: str, visualization: bool, grammar_key: str) -> dict[str, Any]:
    grammar = get_grammar(grammar_key)

    start_total = perf_counter()
    start_lex = perf_counter()
    tokens = grammar.tokenize(source)
    lexical_ms = round((perf_counter() - start_lex) * 1000, 3)

    token_list = [{"type": t.type, "value": t.value, "line": t.line, "column": t.column} for t in tokens if t.type != "EOF"]
    analysis_id = str(uuid4())

    if analysis_level == "tokens":
        return {
            "analysis_id": analysis_id,
            "grammar": grammar.key,
            "tokens": token_list,
            "token_type_count": token_type_summary(tokens),
            "token_count": len(token_list),
            "rule_count": 0,
            "max_depth": 0,
            "node_count": 0,
            "parse_tree": None,
            "parse_tree_summary": "Parse tree unavailable for token-only analysis.",
            "parse_tree_node_counts": {"internal": 0, "leaf": 0, "total": 0},
            "metrics": {},
            "rule_breakdown": {},
            "cost_score": 0.0,
            "cost_breakdown": {"token_term": 0.0, "rule_term": 0.0, "depth_term": 0.0, "node_term": 0.0, "total": 0.0},
            "suggestions": ["[Info] Token-only analysis completed."],
            "hotspots": [],
            "phase_times": {
                "lexical_ms": lexical_ms,
                "parsing_ms": 0.0,
                "total_ms": round((perf_counter() - start_total) * 1000, 3),
            },
        }

    start_parse = perf_counter()
    tree, metrics_summary = grammar.parse_with_metrics(tokens)
    parsing_ms = round((perf_counter() - start_parse) * 1000, 3)

    parse_tree = tree_to_dict(tree) if visualization else None
    parse_tree_for_summary = parse_tree or tree_to_dict(tree)
    tree_summary = summarize_parse_tree(parse_tree_for_summary)
    node_counts = parse_tree_node_counts(parse_tree)

    if analysis_level == "syntax":
        return {
            "analysis_id": analysis_id,
            "grammar": grammar.key,
            "tokens": token_list,
            "token_type_count": token_type_summary(tokens),
            "token_count": metrics_summary["token_count"],
            "rule_count": metrics_summary["total_rule_applications"],
            "max_depth": metrics_summary["max_recursion_depth"],
            "node_count": metrics_summary["parse_tree_nodes"],
            "parse_tree": parse_tree,
            "parse_tree_summary": tree_summary,
            "parse_tree_node_counts": node_counts,
            "metrics": metrics_summary,
            "rule_breakdown": metrics_summary.get("rule_breakdown", {}),
            "cost_score": 0.0,
            "cost_breakdown": {"token_term": 0.0, "rule_term": 0.0, "depth_term": 0.0, "node_term": 0.0, "total": 0.0},
            "suggestions": ["[Info] Syntax-level analysis completed."],
            "hotspots": detect_hotspots(source, metrics_summary),
            "phase_times": {
                "lexical_ms": lexical_ms,
                "parsing_ms": parsing_ms,
                "total_ms": round((perf_counter() - start_total) * 1000, 3),
            },
        }

    cost_score = compute_cost(metrics_summary)
    breakdown = cost_breakdown(metrics_summary)
    suggestions = get_suggestions(metrics_summary, cost_score)

    return {
        "analysis_id": analysis_id,
        "grammar": grammar.key,
        "tokens": token_list,
        "token_type_count": token_type_summary(tokens),
        "token_count": metrics_summary["token_count"],
        "rule_count": metrics_summary["total_rule_applications"],
        "max_depth": metrics_summary["max_recursion_depth"],
        "node_count": metrics_summary["parse_tree_nodes"],
        "parse_tree": parse_tree,
        "parse_tree_summary": tree_summary,
        "parse_tree_node_counts": node_counts,
        "metrics": metrics_summary,
        "rule_breakdown": metrics_summary.get("rule_breakdown", {}),
        "cost_score": cost_score,
        "cost_breakdown": breakdown,
        "suggestions": suggestions,
        "hotspots": detect_hotspots(source, metrics_summary),
        "phase_times": {
            "lexical_ms": lexical_ms,
            "parsing_ms": parsing_ms,
            "total_ms": round((perf_counter() - start_total) * 1000, 3),
        },
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


@app.get("/grammars")
def get_grammars():
    return {"grammars": list_grammars()}


@app.get("/grammar-rules")
def get_grammar_rules(grammar: str = "default"):
    selected = resolve_grammar_or_400(grammar)
    info = selected.info()
    return {
        "grammar": info.key,
        "name": info.name,
        "rules": info.rules,
    }


@app.get("/stats")
def get_stats():
    cache_info = _run_analysis_cached.cache_info()
    return {
        "usage": USAGE_STATS,
        "cache": {
            "hits": cache_info.hits,
            "misses": cache_info.misses,
            "maxsize": cache_info.maxsize,
            "currsize": cache_info.currsize,
        },
    }


@app.get("/history")
def get_history(limit: int = 30):
    if not ANALYSIS_HISTORY_FILE.exists():
        return {"items": []}

    rows: list[dict[str, Any]] = []
    with ANALYSIS_HISTORY_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return {"items": rows[-max(1, min(limit, 200)):][::-1]}


@app.post("/validate-syntax", response_model=SyntaxValidateResponse)
def validate_syntax(request: AnalyzeRequest):
    source = resolve_source(request)
    grammar = resolve_grammar_or_400(request.grammar)
    USAGE_STATS["syntax_validate_calls"] += 1
    _save_usage_stats()

    try:
        tokens = grammar.tokenize(source)
        _, metrics_summary = grammar.parse_with_metrics(tokens)

        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event": "validate-syntax",
            "grammar": grammar.key,
            "token_count": metrics_summary.get("token_count", 0),
        }
        _append_jsonl(USAGE_LOG_FILE, event)

        return {
            "valid": True,
            "token_count": metrics_summary.get("token_count", 0),
            "message": "Syntax is valid.",
            "grammar": grammar.key,
        }
    except SyntaxError as error:
        loc = parse_line_column(str(error))
        raise HTTPException(
            status_code=422,
            detail={"message": f"Syntax validation failed: {error}", **loc},
        )


@app.post("/analyze", response_model=AnalyzeResponse)
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
    source = resolve_source(request)
    grammar = resolve_grammar_or_400(request.grammar)
    USAGE_STATS["analyze_calls"] += 1
    _save_usage_stats()

    before_hits = _run_analysis_cached.cache_info().hits
    try:
        result = _run_analysis_cached(source, request.analysis_level, request.visualization, grammar.key)
    except SyntaxError as error:
        loc = parse_line_column(str(error))
        raise HTTPException(
            status_code=422,
            detail={"message": str(error), **loc},
        )

    after_hits = _run_analysis_cached.cache_info().hits
    if after_hits > before_hits:
        USAGE_STATS["cache_hits"] += 1
        _save_usage_stats()

    source_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
    event = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event": "analyze",
        "analysis_id": result.get("analysis_id"),
        "grammar": grammar.key,
        "analysis_level": request.analysis_level,
        "source_hash": source_hash,
        "source_code": source,
        "token_count": result.get("token_count", 0),
        "rule_count": result.get("rule_count", 0),
        "depth": result.get("max_depth", 0),
        "node_count": result.get("node_count", 0),
        "cost_score": result.get("cost_score", 0),
        "analysis_payload": {
            "analysis_id": result.get("analysis_id"),
            "grammar": result.get("grammar"),
            "tokens": result.get("tokens", []),
            "token_type_count": result.get("token_type_count", {}),
            "token_count": result.get("token_count", 0),
            "rule_count": result.get("rule_count", 0),
            "max_depth": result.get("max_depth", 0),
            "node_count": result.get("node_count", 0),
            "parse_tree": result.get("parse_tree"),
            "parse_tree_summary": result.get("parse_tree_summary", ""),
            "rule_breakdown": result.get("rule_breakdown", {}),
            "cost_score": result.get("cost_score", 0),
            "cost_breakdown": result.get("cost_breakdown", {}),
            "suggestions": result.get("suggestions", []),
            "hotspots": result.get("hotspots", []),
            "phase_times": result.get("phase_times", {}),
        },
    }
    _append_jsonl(USAGE_LOG_FILE, event)
    _append_jsonl(ANALYSIS_HISTORY_FILE, event)

    return result


@app.post("/parse-tree-diff", response_model=ParseTreeDiffResponse)
def parse_tree_diff(request: ParseTreeDiffRequest):
    source_a, source_b = resolve_diff_sources(request)
    grammar = resolve_grammar_or_400(request.grammar)

    USAGE_STATS["parse_tree_diff_calls"] += 1
    _save_usage_stats()

    try:
        tokens_a = grammar.tokenize(source_a)
        tokens_b = grammar.tokenize(source_b)
        tree_a, _ = grammar.parse_with_metrics(tokens_a)
        tree_b, _ = grammar.parse_with_metrics(tokens_b)
    except SyntaxError as error:
        loc = parse_line_column(str(error))
        raise HTTPException(
            status_code=422,
            detail={"message": f"Parse tree diff failed: {error}", **loc},
        )

    tree_a_dict = tree_to_dict(tree_a)
    tree_b_dict = tree_to_dict(tree_b)
    diff_payload = diff_parse_trees(tree_a_dict, tree_b_dict)

    _append_jsonl(USAGE_LOG_FILE, {
        "timestamp": datetime.now(UTC).isoformat(),
        "event": "parse-tree-diff",
        "grammar": grammar.key,
        "summary": diff_payload["summary"],
    })

    return {
        "grammar": grammar.key,
        "summary": diff_payload["summary"],
        "samples": diff_payload["samples"],
        "tree_a": tree_a_dict,
        "tree_b": tree_b_dict,
    }


@app.post("/ai-suggestions", response_model=AISuggestionResponse)
async def ai_suggestions(request: AISuggestionRequest):
    USAGE_STATS["ai_suggestion_calls"] += 1
    _save_usage_stats()

    payload = {
        "code": request.code.strip(),
        "tokens": request.tokens,
        "parse_tree_summary": request.parse_tree_summary.strip() or "Parse tree summary not provided.",
        "cost": request.cost,
        "metrics": request.metrics,
    }

    if not payload["code"]:
        raise HTTPException(status_code=400, detail={"message": "'code' must not be empty.", "line": None, "column": None})

    payload_key = json.dumps(payload, sort_keys=True)

    try:
        suggestions = await asyncio.to_thread(_run_ai_suggestions_cached, payload_key)
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail={"message": str(error), "line": None, "column": None})
    except ValueError as error:
        raise HTTPException(status_code=502, detail={"message": f"Invalid AI response: {error}", "line": None, "column": None})
    except Exception as error:
        raise HTTPException(status_code=500, detail={"message": f"Unexpected AI suggestion error: {error}", "line": None, "column": None})

    _append_jsonl(USAGE_LOG_FILE, {
        "timestamp": datetime.now(UTC).isoformat(),
        "event": "ai-suggestions",
        "summary": {
            "issues": len(suggestions.get("issues", [])),
            "optimizations": len(suggestions.get("optimizations", [])),
        },
    })

    return {"ai_suggestions": suggestions}
