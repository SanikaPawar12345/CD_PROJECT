# cost.py
# Phase 4 – Cost Computation
#
# Computes a normalized scientific "Compiler Cost Score" from the metrics
# collected during lexical, syntactic, and semantic analysis.
#
# SCIENTIFIC MODEL:
# The normalized cost model uses configuration-driven maximum values to normalize
# each metric to [0, 1], then applies weighted scoring to produce a final score
# on a 0-100 scale.
#
# Formula:
#   norm(value, max) = min(value / max, 1.0)
#   
#   cost_score = (
#     w_token * norm(token_count, token_max) +
#     w_depth * norm(max_depth, depth_max) +
#     w_rules * norm(total_rules, rules_max) +
#     w_time * norm(total_time_ms, time_max_ms) +
#     w_memory * norm(peak_memory_kb, memory_max_kb)
#   ) * 100
#
# This ensures:
#   - All metrics are on the same scale [0, 1]
#   - Weights are configuration-driven and can be tuned
#   - Output is always in range [0, 100]
#   - Metrics cannot double-count (no correlated signals)

from . import config


def _normalize_metric(value: float, max_value: float) -> float:
    """
    Normalize a metric to the range [0, 1] using configured maximum value.
    
    Args:
        value: The actual measured value
        max_value: The configured maximum reference value
    
    Returns:
        Normalized value in [0, 1], capped at 1.0 if value exceeds max
    """
    if max_value <= 0:
        return 0.0
    return min(value / max_value, 1.0)


def compute_cost(metrics_summary: dict, total_ms: float = 0.0, peak_memory_kb: float = 0.0) -> float:
    """
    Compute a normalized, scientific cost score from metrics summary and performance data.

    This implements a weighted, normalized scoring model where each metric is
    normalized to [0, 1] using configuration-driven maximums, then combined
    with configurable weights to produce a final score out of 100.

    Args:
        metrics_summary (dict): From Metrics.summary() in metrics.py.
            Expected keys:
                'token_count'             (int)
                'total_rule_applications' (int)
                'max_recursion_depth'     (int)
        total_ms (float): Total pipeline execution time in milliseconds.
        peak_memory_kb (float): Peak memory usage in kilobytes.

    Returns:
        float: Cost score in range [0, 100], rounded to 2 decimal places.
    """
    # Load configuration
    cfg = config.get_config()
    
    # Load weights (must sum to approximately 1.0)
    w_token = cfg.get_weight('token')
    w_depth = cfg.get_weight('depth')
    w_rules = cfg.get_weight('rules')
    w_time = cfg.get_weight('time')
    w_memory = cfg.get_weight('memory')
    
    # Load normalization max values
    token_max = cfg.get_normalization('token_max')
    depth_max = cfg.get_normalization('depth_max')
    rules_max = cfg.get_normalization('rules_max')
    time_max_ms = cfg.get_normalization('time_max_ms')
    memory_max_kb = cfg.get_normalization('memory_max_kb')

    # Extract metrics from summary
    t = metrics_summary['token_count']
    r = metrics_summary['total_rule_applications']
    d = metrics_summary['max_recursion_depth']

    # Normalize each metric to [0, 1]
    norm_token = _normalize_metric(t, token_max)
    norm_depth = _normalize_metric(d, depth_max)
    norm_rules = _normalize_metric(r, rules_max)
    norm_time = _normalize_metric(total_ms, time_max_ms)
    norm_memory = _normalize_metric(peak_memory_kb, memory_max_kb)

    # Compute weighted sum and scale to [0, 100]
    weighted_sum = (
        w_token * norm_token +
        w_depth * norm_depth +
        w_rules * norm_rules +
        w_time * norm_time +
        w_memory * norm_memory
    )
    
    score = weighted_sum * 100.0
    return round(score, 2)


def cost_breakdown(metrics_summary: dict, total_ms: float = 0.0, peak_memory_kb: float = 0.0) -> dict:
    """
    Return detailed cost breakdown showing normalized values and contributions.

    Useful for analytics dashboards and understanding which metrics are driving
    the overall cost score.

    Args:
        metrics_summary (dict): From Metrics.summary() in metrics.py.
        total_ms (float): Total pipeline execution time in milliseconds.
        peak_memory_kb (float): Peak memory usage in kilobytes.

    Returns:
        dict with keys:
            'raw_values': {token_count, depth, rules, time_ms, memory_kb}
            'normalized_values': {token, depth, rules, time, memory} in [0,1]
            'weights': {token, depth, rules, time, memory}
            'contributions': {token_pct, depth_pct, rules_pct, time_pct, memory_pct}
            'total': Final score out of 100
    """
    # Load configuration
    cfg = config.get_config()
    
    # Load weights
    w_token = cfg.get_weight('token')
    w_depth = cfg.get_weight('depth')
    w_rules = cfg.get_weight('rules')
    w_time = cfg.get_weight('time')
    w_memory = cfg.get_weight('memory')
    
    # Load normalization max values
    token_max = cfg.get_normalization('token_max')
    depth_max = cfg.get_normalization('depth_max')
    rules_max = cfg.get_normalization('rules_max')
    time_max_ms = cfg.get_normalization('time_max_ms')
    memory_max_kb = cfg.get_normalization('memory_max_kb')

    # Extract metrics
    t = metrics_summary['token_count']
    r = metrics_summary['total_rule_applications']
    d = metrics_summary['max_recursion_depth']

    # Normalize each metric
    norm_token = _normalize_metric(t, token_max)
    norm_depth = _normalize_metric(d, depth_max)
    norm_rules = _normalize_metric(r, rules_max)
    norm_time = _normalize_metric(total_ms, time_max_ms)
    norm_memory = _normalize_metric(peak_memory_kb, memory_max_kb)

    # Compute weighted contributions
    token_contrib = w_token * norm_token
    depth_contrib = w_depth * norm_depth
    rules_contrib = w_rules * norm_rules
    time_contrib = w_time * norm_time
    memory_contrib = w_memory * norm_memory

    # Calculate total weighted score
    total_weighted = token_contrib + depth_contrib + rules_contrib + time_contrib + memory_contrib
    score_100 = total_weighted * 100.0

    # Calculate percentage contributions
    if total_weighted > 0:
        token_pct = round((token_contrib / total_weighted) * 100, 1)
        depth_pct = round((depth_contrib / total_weighted) * 100, 1)
        rules_pct = round((rules_contrib / total_weighted) * 100, 1)
        time_pct = round((time_contrib / total_weighted) * 100, 1)
        memory_pct = round((memory_contrib / total_weighted) * 100, 1)
    else:
        token_pct = depth_pct = rules_pct = time_pct = memory_pct = 0.0

    return {
        'raw_values': {
            'token_count': t,
            'depth': d,
            'rules': r,
            'time_ms': round(total_ms, 3),
            'memory_kb': round(peak_memory_kb, 2),
        },
        'normalized_values': {
            'token': round(norm_token, 3),
            'depth': round(norm_depth, 3),
            'rules': round(norm_rules, 3),
            'time': round(norm_time, 3),
            'memory': round(norm_memory, 3),
        },
        'weights': {
            'token': w_token,
            'depth': w_depth,
            'rules': w_rules,
            'time': w_time,
            'memory': w_memory,
        },
        'contributions': {
            'token_pct': token_pct,
            'depth_pct': depth_pct,
            'rules_pct': rules_pct,
            'time_pct': time_pct,
            'memory_pct': memory_pct,
        },
        'total': round(score_100, 2),
    }
