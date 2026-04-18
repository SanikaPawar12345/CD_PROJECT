# main.py
# Phase-Wise Compiler Cost Analyzer – Main Orchestrator
#
# Runs all six phases in order:
#   Phase 1 – Lexical Analysis       (lexer.py)
#   Phase 2 – Syntax Analysis        (parser.py)
#   Phase 3 – Metric Collection      (metrics.py)
#   Phase 4 – Cost Computation       (cost.py)
#   Phase 5 – Refactoring Advisor    (advisor.py)
#   Phase 6 – Visualization          (visualizer.py)
#
# Usage:
#   python main.py input.txt
#   python main.py path/to/your_program.txt
#
# Output files (generated in ./output/):
#   parse_tree.dot          – Graphviz DOT source for the parse tree
#   parse_tree.png          – Rendered parse tree image
#   metrics_chart.png       – Bar chart of compiler metrics

import sys
import os

# ---------------------------------------------------------------------------
#  Make sure Python can find the src package when running from project root
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(__file__))

# Expose FastAPI application for `uvicorn main:app --reload` compatibility.
# `api.py` remains the canonical backend module.
from api import app

from src.lexer     import tokenize
from src.parser    import Parser
from src.cost      import compute_cost, cost_breakdown
from src.advisor   import get_suggestions
from src.visualizer import render_tree, render_metrics_chart


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

SEPARATOR = "=" * 60

def section(title: str) -> None:
    """Print a clearly visible section header."""
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(SEPARATOR)


# ---------------------------------------------------------------------------
#  Main pipeline
# ---------------------------------------------------------------------------

def main() -> None:

    # ------------------------------------------------------------------ #
    #  Argument handling                                                   #
    # ------------------------------------------------------------------ #
    if len(sys.argv) < 2:
        print("Usage:  python main.py <input_file>")
        print("Example: python main.py input.txt")
        sys.exit(1)

    input_file = sys.argv[1]

    if not os.path.isfile(input_file):
        print(f"[Error] Source file not found: '{input_file}'")
        sys.exit(1)

    with open(input_file, 'r', encoding='utf-8') as f:
        source_code = f.read()

    print(SEPARATOR)
    print("   Phase-Wise Compiler Cost Analyzer")
    print("   Structural Refactoring Advisor")
    print(SEPARATOR)
    print(f"\n  Source file : {input_file}")
    print(f"  Lines       : {source_code.count(chr(10)) + 1}")
    print(f"  Characters  : {len(source_code)}")

    # ------------------------------------------------------------------ #
    #  Phase 1 – Lexical Analysis                                         #
    # ------------------------------------------------------------------ #
    section("Phase 1 – Lexical Analysis")

    tokens = tokenize(source_code)

    # Don't count the synthetic EOF token in display
    visible_tokens = [t for t in tokens if t.type != 'EOF']
    print(f"\n  Tokens produced : {len(visible_tokens)}")
    print("\n  Token list:")
    for i, tok in enumerate(visible_tokens, start=1):
        print(f"    [{i:>3}]  {tok.type:<10}  {tok.value!r}")

    # ------------------------------------------------------------------ #
    #  Phase 2 – Syntax Analysis (Recursive Descent Parsing)              #
    # ------------------------------------------------------------------ #
    section("Phase 2 – Syntax Analysis  (Recursive Descent Parser)")

    parser = Parser(tokens)

    try:
        parse_tree = parser.parse()
    except SyntaxError as e:
        print(f"\n  [Syntax Error] {e}")
        sys.exit(1)

    print("\n  Status : Parse successful. Parse tree constructed.")

    # ------------------------------------------------------------------ #
    #  Phase 3 – Metric Collection                                        #
    # ------------------------------------------------------------------ #
    section("Phase 3 – Compiler Metrics")

    metrics_summary = parser.metrics.summary()

    print(f"\n  {'Metric':<30}  {'Value':>8}")
    print(f"  {'-'*38}")
    print(f"  {'Token Count':<30}  {metrics_summary['token_count']:>8}")
    print(f"  {'Total Rule Applications':<30}  {metrics_summary['total_rule_applications']:>8}")
    print(f"  {'Max Recursion Depth':<30}  {metrics_summary['max_recursion_depth']:>8}")
    print(f"  {'Parse Tree Nodes':<30}  {metrics_summary['parse_tree_nodes']:>8}")

    print(f"\n  Rule Breakdown:")
    print(f"  {'Rule':<20}  {'Applications':>12}")
    print(f"  {'-'*34}")
    for rule, count in sorted(metrics_summary['rule_breakdown'].items()):
        print(f"  {rule:<20}  {count:>12}")

    # ------------------------------------------------------------------ #
    #  Phase 4 – Cost Computation                                         #
    # ------------------------------------------------------------------ #
    section("Phase 4 – Cost Score")

    cost_score = compute_cost(metrics_summary)
    breakdown  = cost_breakdown(metrics_summary)

    print(f"\n  Cost formula:")
    print(f"    score = (0.5 × tokens) + (1.0 × rules) + (2.0 × depth) + (0.8 × nodes)")
    print(f"\n  Breakdown:")
    print(f"    Token term       = {breakdown['token_term']:>8}")
    print(f"    Rule term        = {breakdown['rule_term']:>8}")
    print(f"    Depth term       = {breakdown['depth_term']:>8}")
    print(f"    Node term        = {breakdown['node_term']:>8}")
    print(f"    {'─'*26}")
    print(f"    Total Cost Score = {breakdown['total']:>8}")

    # ------------------------------------------------------------------ #
    #  Phase 5 – Refactoring Advisor                                      #
    # ------------------------------------------------------------------ #
    section("Phase 5 – Structural Refactoring Advisor")

    suggestions = get_suggestions(metrics_summary, cost_score)

    print(f"\n  Suggestions ({len(suggestions)}):\n")
    for i, suggestion in enumerate(suggestions, start=1):
        # Wrap long lines at 72 chars for readability
        print(f"  [{i}] {suggestion}\n")

    # ------------------------------------------------------------------ #
    #  Phase 6 – Visualization                                            #
    # ------------------------------------------------------------------ #
    section("Phase 6 – Visualization")

    os.makedirs('output', exist_ok=True)

    print()
    render_tree(parse_tree, output_path='output/parse_tree')
    render_metrics_chart(
        metrics_summary,
        cost_score=cost_score,
        output_path='output/metrics_chart.png'
    )

    # ------------------------------------------------------------------ #
    #  Summary                                                            #
    # ------------------------------------------------------------------ #
    print(f"\n{SEPARATOR}")
    print("  Analysis Complete")
    print(f"  Cost Score   : {cost_score}")
    print(f"  Suggestions  : {len(suggestions)}")
    print(f"  Output files : output/parse_tree.png  |  output/metrics_chart.png")
    print(SEPARATOR)


# ---------------------------------------------------------------------------
#  Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    main()
