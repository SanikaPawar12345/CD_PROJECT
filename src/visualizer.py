# visualizer.py
# Phase 6 – Visualization
#
# Provides two independent visualization functions:
#
#   1.  render_tree()
#       Converts the parse tree into Graphviz DOT format, saves the .dot
#       source file, and renders it to a PNG image.
#       Requires: 'graphviz' Python package  +  Graphviz system binaries.
#       Install: pip install graphviz  AND  https://graphviz.org/download/
#
#   2.  render_metrics_chart()
#       Draws a bar chart of the four key metrics using matplotlib.
#       Requires: 'matplotlib' Python package.
#       Install: pip install matplotlib

import os


# ---------------------------------------------------------------------------
#  Parse Tree → PNG  (Graphviz)
# ---------------------------------------------------------------------------

def _build_dot_lines(lines: list, node, parent_id: int | None, counter: list):
    """
    Recursively walks the parse tree and appends Graphviz DOT statements
    to *lines*.

    Uses a mutable single-element list [counter] to generate unique node IDs
    across all recursive calls without needing a global variable.

    Args:
        lines      : accumulated list of DOT-format strings
        node       : current TreeNode
        parent_id  : integer ID of the parent node (None for root)
        counter    : [int] — mutable counter; counter[0] is incremented per node
    """
    my_id = counter[0]
    counter[0] += 1

    # Sanitise label: replace characters DOT parser would misread
    label = node.label.replace('"', '\\"')

    # Distinguish leaf nodes (tokens) from internal nodes (rules) visually
    if node.is_leaf():
        # Terminals shown as boxes
        lines.append(f'  n{my_id} [label="{label}", shape=box, style=filled, fillcolor=lightyellow];')
    else:
        # Non-terminals shown as ellipses
        lines.append(f'  n{my_id} [label="{label}", shape=ellipse, style=filled, fillcolor=lightblue];')

    # Draw edge from parent to this node
    if parent_id is not None:
        lines.append(f'  n{parent_id} -> n{my_id};')

    # Recurse into all children
    for child in node.children:
        _build_dot_lines(lines, child, my_id, counter)


def generate_dot(parse_tree) -> str:
    """
    Convert the entire parse tree into a Graphviz DOT string.

    The DOT language describes a directed graph.
    Graphviz reads .dot files and renders them as images.

    Args:
        parse_tree: root TreeNode returned by Parser.parse()

    Returns:
        str: complete DOT source as a multi-line string.
    """
    lines = [
        'digraph ParseTree {',
        '  rankdir=TB;',                        # top-to-bottom layout
        '  node [fontname="Helvetica", fontsize=10];',
        '  edge [arrowsize=0.6];',
    ]
    _build_dot_lines(lines, parse_tree, None, [0])
    lines.append('}')
    return '\n'.join(lines)


def render_tree(parse_tree, output_path: str = 'output/parse_tree') -> None:
    """
    Render the parse tree as a PNG image using the graphviz package.

    Steps:
      1. Generate DOT source string from the tree.
      2. Save the .dot file to disk (useful for debugging).
      3. Use graphviz.Source.render() to call the Graphviz binary and
         produce a PNG file.

    The function degrades gracefully: if graphviz is not installed it
    prints a warning and skips rendering instead of crashing.

    Args:
        parse_tree  : root TreeNode
        output_path : path prefix (without extension); e.g. 'output/parse_tree'
                      → produces output/parse_tree.dot and output/parse_tree.png
    """
    try:
        import graphviz
    except ImportError:
        print(
            "[Visualizer] 'graphviz' package not found.  "
            "Run:  pip install graphviz  (and install Graphviz system binaries)."
        )
        return

    # Ensure the output directory exists
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    # Generate DOT content
    dot_source = generate_dot(parse_tree)

    # Save .dot file for manual inspection
    dot_file = output_path + '.dot'
    with open(dot_file, 'w', encoding='utf-8') as f:
        f.write(dot_source)
    print(f"[Visualizer] DOT source saved → {dot_file}")

    # Render to PNG using graphviz Python library
    # cleanup=False → keeps the .dot file on disk after rendering
    src = graphviz.Source(dot_source)
    try:
        rendered = src.render(output_path, format='png', cleanup=False)
        print(f"[Visualizer] Parse tree image saved → {rendered}")
    except graphviz.backend.execute.ExecutableNotFound:
        print(
            "[Visualizer] Graphviz system binary 'dot' was not found in PATH. "
            "DOT file was generated, but PNG rendering was skipped."
        )


# ---------------------------------------------------------------------------
#  Metrics → Bar Chart  (matplotlib)
# ---------------------------------------------------------------------------

def render_metrics_chart(
    metrics_summary: dict,
    cost_score: float = 0.0,
    output_path: str = 'output/metrics_chart.png'
) -> None:
    """
    Draw and save a bar chart showing the four core compilation metrics
    and the computed cost score.

    Args:
        metrics_summary : dict from Metrics.summary()
        cost_score      : float from compute_cost() — displayed as a fifth bar
        output_path     : where to save the PNG image
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print(
            "[Visualizer] 'matplotlib' package not found.  "
            "Run:  pip install matplotlib"
        )
        return

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    # ---- Data --------------------------------------------------------
    labels = [
        'Tokens\nConsumed',
        'Rule\nApplications',
        'Max Recursion\nDepth',
        'Parse Tree\nNodes',
        'Cost\nScore',
    ]
    values = [
        metrics_summary['token_count'],
        metrics_summary['total_rule_applications'],
        metrics_summary['max_recursion_depth'],
        metrics_summary['parse_tree_nodes'],
        cost_score,
    ]
    colours = ['steelblue', 'darkorange', 'seagreen', 'crimson', 'mediumpurple']

    # ---- Plot --------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(labels, values, color=colours, width=0.55, edgecolor='black', linewidth=0.6)

    # Annotate each bar with its numeric value
    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(values) * 0.01,   # small gap above bar
            f'{val}',
            ha='center', va='bottom', fontsize=11, fontweight='bold'
        )

    ax.set_title('Phase-Wise Compiler Cost Metrics', fontsize=15, fontweight='bold', pad=14)
    ax.set_ylabel('Value', fontsize=12)
    ax.set_ylim(0, max(values) * 1.18)   # give headroom above tallest bar
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"[Visualizer] Metrics chart saved → {output_path}")
