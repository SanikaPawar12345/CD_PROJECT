from src.metrics import Metrics
from src.cost import compute_cost, cost_breakdown
from src.advisor import get_suggestions


def test_metrics_summary_and_cost_breakdown():
    metrics = Metrics()
    metrics.token_count = 10
    metrics.record_rule("Program", 0)
    metrics.record_rule("Statement", 1)
    metrics.record_rule("Expr", 2)

    summary = metrics.summary()
    score = compute_cost(summary)
    breakdown = cost_breakdown(summary)

    assert summary["total_rule_applications"] == 3
    assert score == breakdown["total"]
    assert breakdown["token_term"] > 0


def test_advisor_returns_suggestions_list():
    summary = {
        "token_count": 80,
        "total_rule_applications": 120,
        "max_recursion_depth": 12,
        "parse_tree_nodes": 140,
        "rule_breakdown": {
            "Print": 5,
            "Assignment": 8,
            "Expr": 10,
            "Term": 10,
            "Factor": 16,
            "ExprRest": 9,
            "TermRest": 2,
        },
    }

    suggestions = get_suggestions(summary, 220)
    assert len(suggestions) >= 3
    assert any("Hotspot" in text or "Pattern" in text for text in suggestions)
