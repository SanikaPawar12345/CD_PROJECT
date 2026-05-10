import sys
import os
import re
import json
import hashlib
import asyncio
import logging
import urllib.request
import tracemalloc
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
import base64

# Load backend environment variables from project-root .env when available.
load_dotenv(Path(__file__).resolve().parent / ".env")

from src.cost import compute_cost, cost_breakdown
from src.advisor import get_suggestions
from src.semantic import SemanticAnalyzer
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


class CostBreakdownPayload(BaseModel):
    raw_values: dict[str, float]
    normalized_values: dict[str, float]
    weights: dict[str, float]
    contributions: dict[str, float]
    total: float


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
    semantic_analysis: dict[str, Any] | None = None
    cost_score: float
    cost_breakdown: CostBreakdownPayload
    suggestions: list[str]
    hotspots: list[dict[str, Any]]
    phase_times: dict[str, float]
    peak_memory_kb: float | None = None


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
    ai_processing_ms: float = 0.0


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

    if not explanation:
        raise ValueError("AI response is missing 'explanation'.")

    return {
        "issues": issues,
        "optimizations": optimizations,
        "optimized_code": optimized_code,
        "explanation": explanation,
    }


def _validate_optimized_code(original_code: str, optimized_code: str, grammar_key: str = "default") -> tuple[str, bool, str]:
    """
    Validate that optimized code is syntactically and semantically correct.
    
    Args:
        original_code: The original source code
        optimized_code: The AI-optimized code to validate
        grammar_key: Which grammar to use for validation
    
    Returns:
        tuple of (code_to_use, is_valid, validation_message)
        where:
            - code_to_use: Either optimized_code (if valid) or original_code (if invalid)
            - is_valid: True if optimized code passed all validation checks
            - validation_message: Explanation of validation result
    """
    # If no optimized code was generated, return original
    if not optimized_code:
        return original_code, False, "No optimized code was generated."
    
    # If code didn't change, it's valid
    if _normalize_code_text(optimized_code) == _normalize_code_text(original_code):
        return original_code, False, "Optimized code is identical to original."
    
    try:
        grammar = get_grammar(grammar_key)
        
        # Step 1: Retokenize optimized code
        try:
            tokens = grammar.tokenize(optimized_code)
            if not tokens:
                return original_code, False, "Validation failed: Optimized code produces no tokens."
        except Exception as e:
            return original_code, False, f"Validation failed during tokenization: {str(e)}"
        
        # Step 2: Reparse optimized code
        try:
            tree, metrics = grammar.parse_with_metrics(tokens)
            if tree is None:
                return original_code, False, "Validation failed: Optimized code does not parse."
        except Exception as e:
            return original_code, False, f"Validation failed during parsing: {str(e)}"
        
        # Step 3: Run semantic analysis on optimized code
        try:
            semantic_analyzer = SemanticAnalyzer(optimized_code)
            semantic_results = semantic_analyzer.analyze()
            
            # Check for semantic errors (not warnings)
            if semantic_results.get('error_count', 0) > 0:
                errors = semantic_results.get('errors', [])
                error_summary = "; ".join([e.get('message', 'unknown error') for e in errors[:2]])
                return original_code, False, f"Validation failed: Semantic errors in optimized code: {error_summary}"
        except Exception as e:
            return original_code, False, f"Validation failed during semantic analysis: {str(e)}"
        
        # All checks passed
        return optimized_code, True, "Optimized code passed all validation checks."
        
    except Exception as e:
        LOGGER.error("Unexpected error during AI output validation: %s", e)
        return original_code, False, f"Validation encountered an unexpected error: {str(e)}"


def _extract_bullet_points(text: str) -> list[str]:
    bullets: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"^(?:[-*•]|\d+\.)\s+", "", line)
        # Drop section headers that some models include in bullet output.
        normalized = re.sub(r"[*_`#•-]+", "", line).strip()
        normalized = re.sub(r"^[^A-Za-z]+", "", normalized).strip().rstrip(":").strip().lower()
        if normalized in {"issues", "optimizations", "explanation"}:
            continue
        if line:
            bullets.append(line)
    return bullets


def _is_noise_bullet(text: str) -> bool:
    normalized = text.strip().lower()
    if not normalized:
        return True
    if normalized in {"```", "input code:", "optimized code:"}:
        return True
    if normalized.startswith("let me analyze"):
        return True
    if re.match(r"^[a-zA-Z_]\w*\s*=.*;\s*$", text.strip()):
        return True
    if re.match(r"^print\s*\(.*\)\s*;\s*$", text.strip()):
        return True
    return False


def _is_section_marker(text: str) -> bool:
    normalized = re.sub(r"[^A-Za-z]+", "", text).strip().lower()
    return normalized in {
        "issues",
        "issue",
        "optimizations",
        "optimization",
        "optim",
        "explanation",
    }


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[A-Za-z0-9_-]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    return cleaned.strip()


def _normalize_code_text(text: str) -> str:
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    return "\n".join(lines)


def _simplify_expression_text(expr: str) -> tuple[str, list[str]]:
    changes: list[str] = []
    current = re.sub(r"\s+", " ", expr.strip())

    while True:
        previous = current

        # Remove unnecessary parentheses around a single identifier/number.
        current, count = re.subn(r"\(\s*([A-Za-z_]\w*|\d+)\s*\)", r"\1", current)
        if count:
            changes.append("Removed redundant parentheses.")

        current, count = re.subn(r"\b([A-Za-z_]\w*|\d+)\s*\*\s*1\b", r"\1", current)
        if count:
            changes.append("Applied algebraic simplification: expr * 1 -> expr.")

        current, count = re.subn(r"\b1\s*\*\s*([A-Za-z_]\w*|\d+)\b", r"\1", current)
        if count:
            changes.append("Applied algebraic simplification: 1 * expr -> expr.")

        current, count = re.subn(r"\b([A-Za-z_]\w*|\d+)\s*\+\s*0\b", r"\1", current)
        if count:
            changes.append("Applied algebraic simplification: expr + 0 -> expr.")

        current, count = re.subn(r"\b0\s*\+\s*([A-Za-z_]\w*|\d+)\b", r"\1", current)
        if count:
            changes.append("Applied algebraic simplification: 0 + expr -> expr.")

        current, count = re.subn(r"\b([A-Za-z_]\w*|\d+)\s*-\s*0\b", r"\1", current)
        if count:
            changes.append("Applied algebraic simplification: expr - 0 -> expr.")

        current, count = re.subn(
            r"\b([A-Za-z_]\w*|\d+)\s*\*\s*0\b|\b0\s*\*\s*([A-Za-z_]\w*|\d+)\b",
            "0",
            current,
        )
        if count:
            changes.append("Applied dead code elimination: expr * 0 -> 0.")

        def fold_constants(match: re.Match[str]) -> str:
            left = int(match.group(1))
            op = match.group(2)
            right = int(match.group(3))
            if op == "+":
                return str(left + right)
            if op == "-":
                return str(left - right)
            return str(left * right)

        current, count = re.subn(r"(?<![A-Za-z_])(\d+)\s*([+\-*])\s*(\d+)(?![A-Za-z_])", fold_constants, current)
        if count:
            changes.append("Applied constant folding for literal arithmetic.")

        current = re.sub(r"\s+", " ", current).strip()
        if current == previous:
            break

    unique_changes = list(dict.fromkeys(changes))
    return current, unique_changes


def _optimize_basic_code(source_code: str) -> tuple[str, list[str]]:
    optimized_lines: list[str] = []
    optimization_notes: list[str] = []

    for raw_line in source_code.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            optimized_lines.append(raw_line)
            continue

        assignment = re.match(r"^([A-Za-z_]\w*)\s*=\s*(.+?)\s*;\s*$", stripped)
        if assignment:
            identifier = assignment.group(1)
            expression = assignment.group(2)
            simplified_expression, notes = _simplify_expression_text(expression)
            optimized_lines.append(f"{identifier} = {simplified_expression};")
            optimization_notes.extend(notes)
            continue

        optimized_lines.append(stripped)

    unique_notes = list(dict.fromkeys(optimization_notes))
    return "\n".join(optimized_lines), unique_notes


def _extract_structured_ai_payload(response_text: str, original_code: str) -> dict[str, Any]:
    """Parse strict-section model output into issues/optimizations/code/explanation."""
    normalized_text = response_text.replace("\r\n", "\n").strip()
    upper_text = normalized_text.upper()

    section_labels = ["ISSUES:", "OPTIMIZATIONS:", "OPTIMIZED CODE:", "EXPLANATION:"]
    positions = {label: upper_text.find(label) for label in section_labels}

    if any(position < 0 for position in positions.values()):
        return {
            "issues": [],
            "optimizations": [],
            "optimized_code": original_code,
            "explanation": "",
        }

    ordered_sections = sorted(
        ((label, positions[label]) for label in section_labels),
        key=lambda item: item[1],
    )
    sections: dict[str, str] = {}
    for index, (label, start_pos) in enumerate(ordered_sections):
        next_pos = ordered_sections[index + 1][1] if index + 1 < len(ordered_sections) else len(normalized_text)
        body_start = start_pos + len(label)
        sections[label] = normalized_text[body_start:next_pos].strip()

    issues = _extract_bullet_points(sections.get("ISSUES:", ""))
    optimizations = _extract_bullet_points(sections.get("OPTIMIZATIONS:", ""))

    optimized_code = _strip_code_fences(sections.get("OPTIMIZED CODE:", ""))
    if not optimized_code:
        optimized_code = original_code

    explanation_lines = _extract_bullet_points(sections.get("EXPLANATION:", ""))
    explanation = " ".join(explanation_lines).strip()
    if not explanation:
        explanation = _strip_code_fences(sections.get("EXPLANATION:", "")).strip()

    return {
        "issues": issues,
        "optimizations": optimizations,
        "optimized_code": optimized_code,
        "explanation": explanation,
    }


@lru_cache(maxsize=2)
def _discover_hf_router_models(api_key: str) -> list[str]:
    """Discover live router models available to the current HF token."""
    request = urllib.request.Request(
        "https://router.huggingface.co/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))

    discovered: list[str] = []
    for entry in payload.get("data", []):
        model_id = str(entry.get("id", "")).strip()
        providers = entry.get("providers", [])
        if not model_id:
            continue
        if any(str(provider.get("status", "")).lower() == "live" for provider in providers):
            discovered.append(model_id)
        if len(discovered) >= 8:
            break
    return discovered


def _extract_chat_message_text(message: Any) -> str:
    """Extract assistant text from HF chat message payload variants."""
    if message is None:
        return ""

    content = getattr(message, "content", "")
    if isinstance(content, str) and content.strip():
        return content.strip()

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str) and item.strip():
                parts.append(item.strip())
                continue
            if isinstance(item, dict):
                for key in ("text", "content", "value"):
                    value = item.get(key)
                    if isinstance(value, str) and value.strip():
                        parts.append(value.strip())
                        break
        if parts:
            return "\n".join(parts)

    reasoning_content = getattr(message, "reasoning_content", "")
    if isinstance(reasoning_content, str) and reasoning_content.strip():
        return reasoning_content.strip()

    reasoning = getattr(message, "reasoning", "")
    if isinstance(reasoning, str) and reasoning.strip():
        return reasoning.strip()

    return ""


def generate_ai_suggestions(
    code: str,
    tokens: list[dict[str, Any]],
    parse_tree_summary: str,
    cost: dict[str, Any],
    metrics: dict[str, Any],
) -> dict[str, Any]:
    primary_model = "Qwen/Qwen3-Coder-30B-A3B-Instruct"

    def fail(reason: str) -> dict[str, Any]:
        LOGGER.error("AI generation failed: %s", reason)
        raise RuntimeError(reason)

    api_key_env_names = ["HF_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"]
    api_key = ""
    api_key_source = ""
    for env_name in api_key_env_names:
        api_key_value = os.getenv(env_name)
        if api_key_value and api_key_value.strip():
            api_key = api_key_value.strip()
            api_key_source = env_name
            break

    if not api_key:
        return fail("Missing API key. Set HF_API_KEY (preferred), GEMINI_API_KEY, or GOOGLE_API_KEY.")

    configured_model = (os.getenv("HF_MODEL") or "").strip()
    discovered_models: list[str] = []
    try:
        discovered_models = _discover_hf_router_models(api_key)
    except Exception as error:
        LOGGER.warning("AI model discovery failed: %s", error)

    candidate_models: list[str] = []
    candidate_models.append(primary_model)
    if configured_model and configured_model != primary_model:
        candidate_models.append(configured_model)
    for model_name in discovered_models:
        if model_name not in candidate_models:
            candidate_models.append(model_name)

    if not candidate_models:
        return fail(
            "No usable Hugging Face router model found. Set HF_MODEL to a live model id from "
            "https://router.huggingface.co/v1/models for your token."
        )

    LOGGER.info(
        "AI debug: api_key_source=%s key_present=%s configured_model=%s discovered_model=%s candidates=%s",
        api_key_source,
        bool(api_key),
        configured_model or "<none>",
        discovered_models[0] if discovered_models else "<none>",
        candidate_models,
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

    token_count = metrics.get("token_count")
    depth = metrics.get("max_recursion_depth")
    rule_count = metrics.get("total_rule_applications")

    prompt = (
        "You are a senior compiler optimization assistant.\n\n"
        "Your goal is to analyze the given code and provide clear, structured, and concise "
        "optimization insights based on compiler efficiency.\n\n"
        "INPUT CODE:\n"
        f"{code}\n\n"
        "METRICS:\n\n"
        f"* Token Count: {token_count}\n"
        f"* Parse Tree Depth: {depth}\n"
        f"* Rule Count: {rule_count}\n\n"
        "PARSE TREE SUMMARY:\n"
        f"{parse_tree_summary}\n\n"
        "STRICT INSTRUCTIONS:\n\n"
        "1. Perform only meaningful compiler optimizations:\n\n"
        "   * Constant folding (e.g., 3 + 4 * 2 -> 11)\n"
        "   * Algebraic simplification (x * 1 -> x, x + 0 -> x)\n"
        "   * Dead code elimination (x * 0 -> 0)\n"
        "   * Remove redundant computations\n\n"
        "CRITICAL OPTIMIZATION CONSTRAINTS:\n\n"
        "1. DO NOT perform full constant propagation across variables.\n\n"
        "   * Example (NOT allowed):\n"
        "     x = 11;\n"
        "     y = x + 1 -> y = 12\n\n"
        "2. DO NOT evaluate the program to final values.\n\n"
        "   * The output must remain symbolic, not fully computed.\n\n"
        "3. Only allow LOCAL expression simplification:\n\n"
        "   * Constant folding ONLY within a single expression\n"
        "     Example: 3 + 4 * 2 -> 11\n"
        "   * Algebraic simplifications:\n"
        "     x * 1 -> x\n"
        "     x + 0 -> x\n"
        "     x * 0 -> 0\n\n"
        "4. DO NOT replace variables with computed constants if they depend on other variables.\n\n"
        "5. Preserve program structure:\n\n"
        "   * Keep variables unless they are truly redundant\n"
        "   * Do NOT collapse the entire program into numeric assignments\n\n"
        "6. Optimization goal:\n\n"
        "   * Reduce expression complexity\n"
        "   * NOT execute the program\n\n"
        "7. Valid optimization example:\n\n"
        "INPUT:\n"
        "x = 3 + 4 * 2;\n"
        "y = x + 1;\n"
        "b = a + a * 0 + (x * 1);\n\n"
        "OUTPUT:\n"
        "x = 11;\n"
        "y = x + 1;\n"
        "b = a + x;\n\n"
        "8. Invalid optimization (MUST NOT HAPPEN):\n"
        "   x = 11;\n"
        "   y = 12;\n"
        "   z = 230;\n"
        "   a = 288;\n"
        "   b = 299;\n\n"
        "This is program evaluation, not optimization.\n\n"
        "Enforce these constraints strictly.\n\n"
        "2. DO NOT:\n\n"
        "   * Add new variables\n"
        "   * Expand or rewrite the logic unnecessarily\n"
        "   * Introduce unrelated expressions\n\n"
        "3. OPTIMIZED CODE RULES:\n\n"
        "   * Must preserve original behavior\n"
        "   * Must be simpler or equivalent\n"
        "   * Must differ from input ONLY if optimization is possible\n\n"
        "4. IF NO OPTIMIZATION IS POSSIBLE:\n\n"
        "   * Clearly state: This code is already optimized and does not require changes.\n"
        "   * Return the SAME code\n\n"
        "5. OUTPUT MUST BE CLEAN AND PROFESSIONAL:\n\n"
        "   * No unnecessary sentences like Let me analyze...\n"
        "   * No repetition\n"
        "   * No verbose explanations\n\n"
        "OUTPUT FORMAT (STRICT):\n\n"
        "ISSUES:\n\n"
        "* Short, precise bullet points describing inefficiencies\n"
        "* If none, write: No major issues found\n\n"
        "OPTIMIZATIONS:\n\n"
        "* Clearly list applied optimizations\n"
        "* If none, write: No optimizations applied\n\n"
        "OPTIMIZED CODE:\n\n"
        "* Only the final optimized code\n"
        "* No explanation inside this section\n\n"
        "EXPLANATION:\n\n"
        "* 2-3 concise lines explaining what was improved\n"
        "* OR why no optimization was needed\n\n"
        "IMPORTANT:\n\n"
        "* Keep output structured and minimal\n"
        "* Ensure readability and clarity\n"
        "* Do NOT include code inside issues or explanation sections\n\n"
        "Return output strictly in clean bullet points.\n"
        "Do NOT include internal reasoning or tags like <think>.\n"
        "Do NOT include unnecessary explanations.\n\n"
        f"Compiler metrics (readable JSON):\n{json.dumps(metrics_readable, ensure_ascii=True, indent=2)}\n"
    )

    try:
        client = InferenceClient(token=os.getenv("HF_API_KEY"))
    except Exception as error:
        LOGGER.exception("AI generation failed: could not initialize InferenceClient: %s", error)
        return fail(f"Failed to initialize Hugging Face client: {error}")

    response_text = ""
    last_error = ""

    for model_name in candidate_models:
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
                response_text = _extract_chat_message_text(message)
            if response_text.strip():
                break
            last_error = f"Model '{model_name}' returned empty chat content."
        except ValueError as error:
            if model_name == primary_model:
                LOGGER.warning("Primary model chat response unsupported for this request: %s (%s)", model_name, error)
                last_error = f"Model '{model_name}' failed: {error}"
                continue
            try:
                response_text = client.text_generation(
                    prompt=prompt,
                    model=model_name,
                    max_new_tokens=512,
                    temperature=0.2,
                    do_sample=True,
                    return_full_text=False,
                )
                if response_text.strip():
                    break
                last_error = f"Model '{model_name}' returned empty text generation output."
            except Exception as text_error:
                LOGGER.warning("Model candidate failed: %s (%s)", model_name, text_error)
                last_error = f"Model '{model_name}' failed: {text_error}"
                continue
        except (HfHubHTTPError, StopIteration, Exception) as error:
            LOGGER.warning("Model candidate failed: %s (%s)", model_name, error)
            last_error = f"Model '{model_name}' failed: {error}"
            continue

    if not isinstance(response_text, str) or not response_text.strip():
        return fail(last_error or "All Hugging Face model candidates failed.")

    parsed_payload = _extract_structured_ai_payload(response_text, code)
    issues = [
        point for point in parsed_payload.get("issues", [])
        if not _is_section_marker(point) and not _is_noise_bullet(point)
    ]
    optimizations = [
        point for point in parsed_payload.get("optimizations", [])
        if not _is_section_marker(point) and not _is_noise_bullet(point)
    ]
    optimized_code = str(parsed_payload.get("optimized_code", "")).strip() or code
    explanation = str(parsed_payload.get("explanation", "")).strip()

    if not explanation:
        fallback_points = _extract_bullet_points(response_text)
        fallback_points = [
            point for point in fallback_points
            if not _is_section_marker(point) and not _is_noise_bullet(point)
        ]
        explanation = " ".join(fallback_points[:4]).strip()

    if not issues and not optimizations:
        LOGGER.warning(
            "AI generation warning: response had limited structured sections. Falling back to generic extraction. Preview=%s",
            response_text[:200],
        )
        fallback_points = _extract_bullet_points(response_text)
        fallback_points = [
            point for point in fallback_points
            if not _is_section_marker(point) and not _is_noise_bullet(point)
        ]
        issues = fallback_points[:3]
        optimizations = fallback_points[3:9] if len(fallback_points) > 3 else fallback_points

    deterministic_code, deterministic_notes = _optimize_basic_code(code)
    code_was_optimized = _normalize_code_text(deterministic_code) != _normalize_code_text(code)

    model_changed_code = _normalize_code_text(optimized_code) != _normalize_code_text(code)
    if code_was_optimized and not model_changed_code:
        optimized_code = deterministic_code
        if not optimizations:
            optimizations = deterministic_notes
        if not issues:
            issues = [
                "Detected algebraic and dead-code simplification opportunities in the input expression chain."
            ]

    if not code_was_optimized and not model_changed_code:
        already_message = "This code is already optimized and does not require changes."
        issues = []
        optimizations = [already_message]
        optimized_code = ""
        explanation = already_message

    payload = {
        "issues": issues,
        "optimizations": optimizations,
        "optimized_code": optimized_code,
        "explanation": explanation or "Suggestions generated from compiler analysis context.",
    }
    
    # Validate optimized code before returning
    if optimized_code:
        validated_code, is_valid, validation_msg = _validate_optimized_code(code, optimized_code, grammar_key="default")
        if not is_valid:
            # Optimization failed validation; use original code and add validation warning
            LOGGER.warning("AI optimization rejected: %s", validation_msg)
            payload["optimized_code"] = ""
            if not payload["issues"]:
                payload["issues"] = [f"⚠️ Optimization validation failed: {validation_msg}"]
            else:
                payload["issues"].insert(0, f"⚠️ Optimization validation failed: {validation_msg}")
    
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


def _invalid_grammar_input_error(message: str) -> HTTPException:
    return HTTPException(status_code=400, detail={"message": message, "line": None, "column": None})


def _validate_default_input(source: str) -> None:
    lowered = source.lower()
    if re.search(r"\bint\b|\bprintf\b|\breturn\b|[{}]", lowered):
        raise _invalid_grammar_input_error(
            "Invalid input for selected grammar: Expected expression syntax but received C-style syntax."
        )

    if re.search(r"[|?\[\]]", source):
        raise _invalid_grammar_input_error(
            "Invalid input for selected grammar: Expected expression syntax but received regex-like pattern."
        )

    statements = [segment.strip() for segment in source.split(';') if segment.strip()]
    if not statements:
        raise _invalid_grammar_input_error(
            "Invalid input for selected grammar: Expected assignment/print statements ending with ';'."
        )

    valid_stmt = re.compile(r"^(?:[A-Za-z_]\w*\s*=\s*.*|print\s*\(\s*.*\s*\))$", re.IGNORECASE)
    if any(not valid_stmt.match(stmt) for stmt in statements):
        raise _invalid_grammar_input_error(
            "Invalid input for selected grammar: Expected assignment/print expression statements."
        )


def _validate_c_input(source: str) -> None:
    lowered = source.lower()

    if 'print(' in lowered:
        raise _invalid_grammar_input_error(
            "Invalid input for selected grammar: Expected C code but received expression syntax."
        )

    if ';' not in source:
        raise _invalid_grammar_input_error(
            "Invalid input for selected grammar: Expected C code with ';' terminated statements."
        )

    if not re.search(r"\b(int|printf|return)\b", lowered):
        raise _invalid_grammar_input_error(
            "Invalid input for selected grammar: Expected C code but received expression syntax."
        )

    looks_like_regex = (
        '\n' not in source
        and ';' not in source
        and '=' not in source
        and '{' not in source
        and '}' not in source
        and re.fullmatch(r"[A-Za-z0-9()|*+?.\[\]\\]+", source.strip()) is not None
    )
    if looks_like_regex:
        raise _invalid_grammar_input_error(
            "Invalid input for selected grammar: Expected C code but received regex pattern."
        )


def _validate_regex_input(source: str) -> None:
    if '\n' in source or '\r' in source:
        raise _invalid_grammar_input_error(
            "Invalid input for selected grammar: Regex grammar accepts only a single-line pattern."
        )

    lowered = source.lower()
    if re.search(r"\b(int|print|printf|return)\b", lowered):
        raise _invalid_grammar_input_error(
            "Invalid input for selected grammar: Expected regex pattern but received programming-language keywords."
        )

    if re.search(r"[=;{}]", source):
        raise _invalid_grammar_input_error(
            "Invalid input for selected grammar: Expected regex pattern but received statement syntax."
        )

    if re.fullmatch(r"[A-Za-z0-9()|*+?.\[\]\\]+", source.strip()) is None:
        raise _invalid_grammar_input_error(
            "Invalid input for selected grammar: Regex contains unsupported characters."
        )


def validate_input_by_grammar(source: str, grammar_key: str) -> None:
    normalized = (grammar_key or "default").strip().lower()
    if normalized == "default":
        _validate_default_input(source)
        return
    if normalized == "c":
        _validate_c_input(source)
        return
    if normalized == "regex":
        _validate_regex_input(source)
        return


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

    # Start memory and timing measurements
    tracemalloc.start()
    start_total = perf_counter()
    start_lex = perf_counter()
    
    tokens = grammar.tokenize(source)
    lexical_ms = round((perf_counter() - start_lex) * 1000, 3)

    token_list = [{"type": t.type, "value": t.value, "line": t.line, "column": t.column} for t in tokens if t.type != "EOF"]
    analysis_id = str(uuid4())

    if analysis_level == "tokens":
        peak_memory_kb = round(tracemalloc.get_traced_memory()[1] / 1024, 2)
        tracemalloc.stop()
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
            "cost_breakdown": {"token_term": 0.0, "rule_term": 0.0, "depth_term": 0.0, "total": 0.0},
            "suggestions": ["[Info] Token-only analysis completed."],
            "hotspots": [],
            "phase_times": {
                "lexical_ms": lexical_ms,
                "parsing_ms": 0.0,
                "total_ms": round((perf_counter() - start_total) * 1000, 3),
            },
            "peak_memory_kb": peak_memory_kb,
        }

    start_parse = perf_counter()
    tree, metrics_summary = grammar.parse_with_metrics(tokens)
    parsing_ms = round((perf_counter() - start_parse) * 1000, 3)

    # Run semantic analysis
    start_semantic = perf_counter()
    semantic_analyzer = SemanticAnalyzer(source)
    semantic_analysis = semantic_analyzer.analyze()
    semantic_ms = round((perf_counter() - start_semantic) * 1000, 3)

    parse_tree = tree_to_dict(tree) if visualization else None
    parse_tree_for_summary = parse_tree or tree_to_dict(tree)
    tree_summary = summarize_parse_tree(parse_tree_for_summary)
    node_counts = parse_tree_node_counts(parse_tree)

    if analysis_level == "syntax":
        peak_memory_kb = round(tracemalloc.get_traced_memory()[1] / 1024, 2)
        tracemalloc.stop()
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
            "semantic_analysis": semantic_analysis,
            "cost_score": 0.0,
            "cost_breakdown": {"token_term": 0.0, "rule_term": 0.0, "depth_term": 0.0, "total": 0.0},
            "suggestions": ["[Info] Syntax-level analysis completed."],
            "hotspots": detect_hotspots(source, metrics_summary),
            "phase_times": {
                "lexical_ms": lexical_ms,
                "parsing_ms": parsing_ms,
                "semantic_ms": semantic_ms,
                "total_ms": round((perf_counter() - start_total) * 1000, 3),
            },
            "peak_memory_kb": peak_memory_kb,
        }

    cost_score = compute_cost(metrics_summary, total_ms=0.0, peak_memory_kb=0.0)
    breakdown = cost_breakdown(metrics_summary, total_ms=0.0, peak_memory_kb=0.0)
    suggestions = get_suggestions(metrics_summary, cost_score)

    peak_memory_kb = round(tracemalloc.get_traced_memory()[1] / 1024, 2)
    tracemalloc.stop()

    # Recompute cost with real timing data
    total_ms = round((perf_counter() - start_total) * 1000, 3)
    cost_score = compute_cost(metrics_summary, total_ms=total_ms, peak_memory_kb=peak_memory_kb)
    breakdown = cost_breakdown(metrics_summary, total_ms=total_ms, peak_memory_kb=peak_memory_kb)

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
        "semantic_analysis": semantic_analysis,
        "cost_score": cost_score,
        "cost_breakdown": breakdown,
        "suggestions": suggestions,
        "hotspots": detect_hotspots(source, metrics_summary),
        "phase_times": {
            "lexical_ms": lexical_ms,
            "parsing_ms": parsing_ms,
            "semantic_ms": semantic_ms,
            "total_ms": total_ms,
        },
        "peak_memory_kb": peak_memory_kb,
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
    validate_input_by_grammar(source, grammar.key)
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
    validate_input_by_grammar(source, grammar.key)
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
    validate_input_by_grammar(source_a, grammar.key)
    validate_input_by_grammar(source_b, grammar.key)

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

    start_ai = perf_counter()
    try:
        suggestions = await asyncio.to_thread(_run_ai_suggestions_cached, payload_key)
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail={"message": str(error), "line": None, "column": None})
    except ValueError as error:
        raise HTTPException(status_code=502, detail={"message": f"Invalid AI response: {error}", "line": None, "column": None})
    except Exception as error:
        raise HTTPException(status_code=500, detail={"message": f"Unexpected AI suggestion error: {error}", "line": None, "column": None})
    
    ai_processing_ms = round((perf_counter() - start_ai) * 1000, 3)

    _append_jsonl(USAGE_LOG_FILE, {
        "timestamp": datetime.now(UTC).isoformat(),
        "event": "ai-suggestions",
        "summary": {
            "issues": len(suggestions.get("issues", [])),
            "optimizations": len(suggestions.get("optimizations", [])),
            "ai_processing_ms": ai_processing_ms,
        },
    })

    suggestions["ai_processing_ms"] = ai_processing_ms
    return {"ai_suggestions": suggestions}


@app.post("/compare")
def compare(payload: dict):
    """Compare original and optimized code by running full analysis on both and returning a summary."""
    original = str(payload.get("original_code", "") or "").strip()
    optimized = str(payload.get("optimized_code", "") or "").strip()
    grammar_key = str(payload.get("grammar", "default") or "default")

    if not original:
        raise HTTPException(status_code=400, detail={"message": "Provide 'original_code' in payload.", "line": None, "column": None})

    # Validate grammar keys and inputs for both programs
    grammar = resolve_grammar_or_400(grammar_key)
    try:
        validate_input_by_grammar(original, grammar.key)
    except HTTPException as he:
        raise he

    # Analyze original
    try:
        original_result = _run_analysis_cached(original, "full", True, grammar.key)
    except SyntaxError as error:
        loc = parse_line_column(str(error))
        raise HTTPException(status_code=422, detail={"message": str(error), **loc})

    optimized_result = None
    if optimized:
        # Validate optimized against same grammar
        try:
            validate_input_by_grammar(optimized, grammar.key)
            optimized_result = _run_analysis_cached(optimized, "full", True, grammar.key)
        except HTTPException:
            # If optimized fails validation, return original and include validation note
            optimized_result = None

    # Compute simple reductions
    def safe_num(v):
        try:
            return float(v or 0)
        except Exception:
            return 0.0

    orig_cost = safe_num(original_result.get("cost_score", 0))
    opt_cost = safe_num(optimized_result.get("cost_score", orig_cost)) if optimized_result else orig_cost
    orig_time = safe_num(original_result.get("phase_times", {}).get("total_ms", 0))
    opt_time = safe_num(optimized_result.get("phase_times", {}).get("total_ms", orig_time)) if optimized_result else orig_time
    orig_mem = safe_num(original_result.get("peak_memory_kb", 0))
    opt_mem = safe_num(optimized_result.get("peak_memory_kb", orig_mem)) if optimized_result else orig_mem

    def pct_reduction(base, new):
        if base <= 0:
            return 0.0
        return round(((base - new) / base) * 100.0, 3)

    comparison = {
        "cost_reduction_pct": pct_reduction(orig_cost, opt_cost),
        "time_reduction_pct": pct_reduction(orig_time, opt_time),
        "memory_reduction_pct": pct_reduction(orig_mem, opt_mem),
        "orig_cost": orig_cost,
        "opt_cost": opt_cost,
        "orig_time_ms": orig_time,
        "opt_time_ms": opt_time,
        "orig_memory_kb": orig_mem,
        "opt_memory_kb": opt_mem,
    }

    return {
        "original": original_result,
        "optimized": optimized_result,
        "comparison": comparison,
    }


@app.post("/export-report")
def export_report(payload: dict):
    """Save analysis report and provided images into a timestamped reports folder."""
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    folder = reports_dir / f"analysis_{ts}"
    folder.mkdir(parents=True, exist_ok=True)

    original_code = payload.get("original_code")
    optimized_code = payload.get("optimized_code")
    original_analysis = payload.get("original_analysis")
    optimized_analysis = payload.get("optimized_analysis")
    comparison = payload.get("comparison")
    ai = payload.get("ai_suggestions")

    def safe_write(name, content):
        path = folder / name
        path.write_text(json.dumps(content, indent=2) if not isinstance(content, str) else content, encoding="utf-8")
        return str(path)

    files_written = {}
    if original_code:
        files_written["original_code.txt"] = safe_write("original_code.txt", original_code)
    if optimized_code:
        files_written["optimized_code.txt"] = safe_write("optimized_code.txt", optimized_code)
    if original_analysis:
        files_written["original_analysis.json"] = safe_write("original_analysis.json", original_analysis)
    if optimized_analysis:
        files_written["optimized_analysis.json"] = safe_write("optimized_analysis.json", optimized_analysis)
    if comparison:
        files_written["comparison.json"] = safe_write("comparison.json", comparison)
    if ai:
        files_written["ai_suggestions.json"] = safe_write("ai_suggestions.json", ai)

    # Save images if present (expected as list of {name, data})
    images = payload.get("images") or []
    saved_images = []
    for img in images:
        name = img.get("name") or f"image_{len(saved_images)}.png"
        data = img.get("data") or ""
        try:
            header, b64 = (data.split(",", 1) + [""])[:2]
            raw = base64.b64decode(b64 or data)
            p = folder / name
            p.open("wb").write(raw)
            saved_images.append(str(p))
        except Exception:
            continue

    # Generate a simple Markdown summary
    md_lines = [
        f"# Analysis Report - {ts}",
        "",
        "## Summary",
    ]
    if comparison:
        md_lines += [
            f"- Cost reduction: {comparison.get('cost_reduction_pct')}%",
            f"- Time reduction: {comparison.get('time_reduction_pct')}%",
            f"- Memory reduction: {comparison.get('memory_reduction_pct')}%",
        ]
    md_lines += ["", "## Files", ""]
    for name, path in files_written.items():
        md_lines.append(f"- {name}: {path}")
    for img_path in saved_images:
        md_lines.append(f"- Image: {img_path}")

    (folder / "report.md").write_text("\n".join(md_lines), encoding="utf-8")

    return {"folder": str(folder), "files": files_written, "images": saved_images}
