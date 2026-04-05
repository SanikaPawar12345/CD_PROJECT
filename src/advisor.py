# advisor.py
# Phase 5 – Structural Refactoring Advisor
#
# Analyzes the metrics summary and cost score using a purely rule-based
# approach (if/else threshold checks). No machine learning or AI is used.
#
# Each rule checks one metric against a threshold:
#   - If the metric exceeds the threshold → a suggestion is added.
#   - If no rule triggers → the program is deemed structurally clean.
#
# Rules defined below can be adjusted by changing the threshold constants.


# ---------------------------------------------------------------------------
#  Threshold constants  (tweak these to tune advice sensitivity)
# ---------------------------------------------------------------------------
TOKEN_HIGH        = 30    # Token count above this → complex expression warning
RULE_HIGH         = 50    # Rule applications above this → grammar complexity warning
DEPTH_HIGH        = 10    # Recursion depth above this → nesting depth warning
NODE_HIGH         = 60    # Parse tree nodes above this → structural size warning
COST_HIGH         = 100   # Cost score above this → overall complexity warning
PRINT_HEAVY       = 3     # More than this many 'Print' rules → excessive output warning
ASSIGN_HEAVY      = 5     # More than this many 'Assignment' rules → variable bloat


def get_suggestions(metrics_summary: dict, cost_score: float) -> list[str]:
    """
    Apply all advisory rules and return a list of suggestion strings.

    Each suggestion is a self-contained, human-readable sentence explaining:
      - Which metric triggered the rule.
      - What the measured value was.
      - What the programmer might consider doing.

    Args:
        metrics_summary (dict): From Metrics.summary() in metrics.py.
        cost_score      (float): From compute_cost() in cost.py.

    Returns:
        list[str]: One string per triggered rule. Never empty —
                   at least one "optimal" message is always returned.
    """
    suggestions: list[str] = []

    t = metrics_summary['token_count']
    r = metrics_summary['total_rule_applications']
    d = metrics_summary['max_recursion_depth']
    n = metrics_summary['parse_tree_nodes']
    rb = metrics_summary['rule_breakdown']  # per-rule counts

    # ------------------------------------------------------------------
    #  Rule 1: High token count → expressions may be too complex
    # ------------------------------------------------------------------
    if t > TOKEN_HIGH:
        suggestions.append(
            f"[Token Complexity] {t} tokens detected (threshold: {TOKEN_HIGH}). "
            "Consider breaking long expressions into named intermediate variables "
            "to reduce per-line complexity and improve readability."
        )

    # ------------------------------------------------------------------
    #  Rule 2: High rule applications → many grammar expansions
    # ------------------------------------------------------------------
    if r > RULE_HIGH:
        suggestions.append(
            f"[Grammar Complexity] {r} grammar rule applications "
            f"(threshold: {RULE_HIGH}). "
            "The program may contain deeply nested or heavily chained expressions. "
            "Flattening nested arithmetic can reduce parse work."
        )

    # ------------------------------------------------------------------
    #  Rule 3: Deep recursion → heavy call-stack usage
    # ------------------------------------------------------------------
    if d > DEPTH_HIGH:
        suggestions.append(
            f"[Recursion Depth] Maximum parse depth reached: {d} "
            f"(threshold: {DEPTH_HIGH}). "
            "Deeply nested expressions (e.g. ((a + (b * c)))) increase stack frames. "
            "Prefer flat expressions where possible."
        )

    # ------------------------------------------------------------------
    #  Rule 4: Large parse tree → structural bulk
    # ------------------------------------------------------------------
    if n > NODE_HIGH:
        suggestions.append(
            f"[Tree Size] Parse tree has {n} nodes (threshold: {NODE_HIGH}). "
            "A large tree indicates high structural complexity. "
            "Consider refactoring repeated patterns into separate statements."
        )

    # ------------------------------------------------------------------
    #  Rule 5: High overall cost score
    # ------------------------------------------------------------------
    if cost_score > COST_HIGH:
        suggestions.append(
            f"[High Cost Score] Computed score = {cost_score} "
            f"(threshold: {COST_HIGH}). "
            "Multiple metrics are elevated. Review the full metric report and "
            "apply the individual suggestions above."
        )

    # ------------------------------------------------------------------
    #  Rule 6: Excessive print statements → noisy output
    # ------------------------------------------------------------------
    print_count = rb.get('Print', 0)
    if print_count > PRINT_HEAVY:
        suggestions.append(
            f"[Print Heavy] {print_count} print statements found "
            f"(threshold: {PRINT_HEAVY}). "
            "Consolidate output into fewer, more structured print calls."
        )

    # ------------------------------------------------------------------
    #  Rule 7: Too many assignment statements → variable proliferation
    # ------------------------------------------------------------------
    assign_count = rb.get('Assignment', 0)
    if assign_count > ASSIGN_HEAVY:
        suggestions.append(
            f"[Variable Proliferation] {assign_count} assignment statements "
            f"(threshold: {ASSIGN_HEAVY}). "
            "Consider whether all intermediate variables are necessary, "
            "or if some can be inlined."
        )

    # ------------------------------------------------------------------
    #  Rule 8: Hotspot detection from expression-heavy grammar paths
    # ------------------------------------------------------------------
    expr_count = rb.get('Expr', 0)
    term_count = rb.get('Term', 0)
    factor_count = rb.get('Factor', 0)
    if expr_count >= 8 and factor_count >= 10:
        suggestions.append(
            "[Complexity Hotspot] Expression parsing appears dense "
            f"(Expr={expr_count}, Term={term_count}, Factor={factor_count}). "
            "Split large arithmetic chains into smaller statements to reduce cognitive and parse complexity."
        )

    # ------------------------------------------------------------------
    #  Rule 9: Potential grammar misuse pattern warning
    # ------------------------------------------------------------------
    expr_rest = rb.get('ExprRest', 0)
    term_rest = rb.get('TermRest', 0)
    if expr_rest > term_rest * 2 and expr_rest >= 6:
        suggestions.append(
            "[Rule Misuse Warning] Addition chaining dominates multiplication structure "
            f"(ExprRest={expr_rest}, TermRest={term_rest}). "
            "Review expression grouping; explicit parentheses can improve intent and stability."
        )

    # ------------------------------------------------------------------
    #  Rule 10: Pattern simplification guidance
    # ------------------------------------------------------------------
    if d >= 6 and n >= 30:
        suggestions.append(
            "[Pattern Simplification] Nested expressions are likely driving tree growth. "
            "Use temporary variables for repeated subexpressions and flatten unnecessary nesting."
        )

    # ------------------------------------------------------------------
    #  Default: no issues found
    # ------------------------------------------------------------------
    if not suggestions:
        suggestions.append(
            "[Optimal] All metrics are within acceptable thresholds. "
            "No structural refactoring is recommended for this program."
        )

    return suggestions
