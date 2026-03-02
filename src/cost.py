# cost.py
# Phase 4 – Cost Computation
#
# Computes a single numeric "Compiler Cost Score" from the metrics
# collected during lexical and syntactic analysis.
#
# Formula:
#   cost = (W1 * token_count)
#        + (W2 * total_rule_applications)
#        + (W3 * max_recursion_depth)
#        + (W4 * parse_tree_nodes)
#
# Weight rationale:
#   W1 = 0.5  → Token count is cheap; the lexer is a simple scan.
#   W2 = 1.0  → Each rule application is one function call + node alloc.
#   W3 = 2.0  → Deep recursion stresses the call stack the most.
#   W4 = 0.8  → Each tree node is a heap allocation; significant but less
#                than a full function call overhead.
#
# The score is intentionally dimensionless — it is a relative complexity
# indicator, not a measurement in real CPU cycles.


# Weight constants (tunable)
W1 = 0.5   # Token count weight
W2 = 1.0   # Rule applications weight
W3 = 2.0   # Max recursion depth weight
W4 = 0.8   # Parse tree node count weight


def compute_cost(metrics_summary: dict) -> float:
    """
    Compute the weighted cost score from a metrics summary dict.

    Args:
        metrics_summary (dict): Produced by Metrics.summary() in metrics.py.
            Expected keys:
                'token_count'             (int)
                'total_rule_applications' (int)
                'max_recursion_depth'     (int)
                'parse_tree_nodes'        (int)

    Returns:
        float: The rounded cost score (2 decimal places).
    """
    t = metrics_summary['token_count']             # lexer output size
    r = metrics_summary['total_rule_applications'] # parser work done
    d = metrics_summary['max_recursion_depth']     # call stack pressure
    n = metrics_summary['parse_tree_nodes']        # memory allocated

    score = (W1 * t) + (W2 * r) + (W3 * d) + (W4 * n)
    return round(score, 2)


def cost_breakdown(metrics_summary: dict) -> dict:
    """
    Return each weighted term individually for display purposes.

    Useful if you want to show *which* metric is contributing the most.

    Returns:
        dict with keys: 'token_term', 'rule_term', 'depth_term', 'node_term', 'total'
    """
    t = metrics_summary['token_count']
    r = metrics_summary['total_rule_applications']
    d = metrics_summary['max_recursion_depth']
    n = metrics_summary['parse_tree_nodes']

    return {
        'token_term': round(W1 * t, 2),
        'rule_term':  round(W2 * r, 2),
        'depth_term': round(W3 * d, 2),
        'node_term':  round(W4 * n, 2),
        'total':      round((W1 * t) + (W2 * r) + (W3 * d) + (W4 * n), 2),
    }
