# metrics.py
# Phase 3 – Metric Collection
#
# Defines the Metrics class, which is instantiated once per parse run.
# The parser calls record_rule() on every grammar function it enters,
# and increments token_count on every consume() call.
#
# Tracked metrics:
#   token_count          – how many tokens were consumed (lexer output size)
#   rule_applications    – dict mapping rule name → call count
#   max_depth            – deepest recursion level reached during parsing
#   node_count           – total TreeNode objects created (= rule call count)


class Metrics:
    """
    Records all measurable data produced during lexical and
    syntactic analysis phases.

    Passed to:
      - cost.py      → to compute a weighted cost score
      - advisor.py   → to generate refactoring suggestions
      - visualizer.py → to produce a metric bar chart
    """

    def __init__(self):
        # Count of tokens consumed by the parser (excludes EOF)
        self.token_count: int = 0

        # Tracks how many times each grammar rule function was called.
        # Example: {'Expr': 4, 'Term': 4, 'Factor': 4, ...}
        self.rule_applications: dict[str, int] = {}

        # The deepest recursion level reached.
        # Depth 0 = Program, depth 1 = StatementList, etc.
        self.max_depth: int = 0

        # Total parse tree nodes created.
        # This equals total rule_applications (one node per rule entry).
        self.node_count: int = 0

    # ------------------------------------------------------------------
    #  Called by parser grammar functions
    # ------------------------------------------------------------------

    def record_rule(self, rule_name: str, depth: int) -> None:
        """
        Record one entry into a grammar rule.

        Called at the top of every parse_* method in parser.py.

        Args:
            rule_name (str): Name of the grammar rule (e.g. 'Expr').
            depth     (int): Current recursion depth passed down from caller.
        """
        # Increment call count for this rule
        self.rule_applications[rule_name] = (
            self.rule_applications.get(rule_name, 0) + 1
        )

        # Update maximum depth if this call is deeper than all previous
        if depth > self.max_depth:
            self.max_depth = depth

        # Each rule entry corresponds to one TreeNode being constructed
        self.node_count += 1

    # ------------------------------------------------------------------
    #  Aggregation helpers
    # ------------------------------------------------------------------

    def total_rule_applications(self) -> int:
        """Return the sum of all individual rule call counts."""
        return sum(self.rule_applications.values())

    def summary(self) -> dict:
        """
        Return a plain dictionary snapshot of all metrics.

        This dict is passed to cost.py and advisor.py so they stay
        decoupled from the Metrics object itself.
        """
        return {
            'token_count':            self.token_count,
            'total_rule_applications': self.total_rule_applications(),
            'max_recursion_depth':    self.max_depth,
            'parse_tree_nodes':       self.node_count,
            'rule_breakdown':         dict(self.rule_applications),
        }
