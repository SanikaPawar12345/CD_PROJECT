# parser.py
# Phase 2 – Syntax Analysis
#
# Implements a hand-written Recursive Descent Parser.
# No parser-generator library is used (no PLY, ANTLR, Lark, etc.)
#
# The grammar used is a LEFT-RECURSION-FREE version of the original spec,
# because recursive descent cannot handle left recursion directly.
#
# Original grammar:
#   Expr → Expr + Term | Term          ← left-recursive, unusable as-is
#   Term → Term * Factor | Factor      ← left-recursive, unusable as-is
#
# Transformed (right-recursive / iterative tail form):
#   Expr     → Term ExprRest
#   ExprRest → + Term ExprRest | ε
#   Term     → Factor TermRest
#   TermRest → * Factor TermRest | ε
#
# Full grammar implemented here:
#
#   Program       → StatementList
#   StatementList → Statement StatementList | ε
#   Statement     → Assignment | Print
#   Assignment    → id = Expr ;
#   Print         → print ( Expr ) ;
#   Expr          → Term ExprRest
#   ExprRest      → + Term ExprRest | ε
#   Term          → Factor TermRest
#   TermRest      → * Factor TermRest | ε
#   Factor        → ( Expr ) | id | number
#
# Each grammar rule is a method: parse_<rule>(depth)
# 'depth' is passed down to Metrics for recursion-depth tracking.
#
# How nodes get into the tree:
#   - Internal nodes  → created at start of each parse_* method
#   - Terminal nodes  → created when consume() returns a token

from src.tree import TreeNode
from src.metrics import Metrics


class Parser:
    """
    Recursive Descent Parser.

    Usage:
        parser = Parser(tokens)       # tokens from lexer.tokenize()
        tree   = parser.parse()       # returns root TreeNode
        report = parser.metrics.summary()
    """

    def __init__(self, tokens: list):
        self.tokens = tokens    # Full token list from the lexer
        self.pos = 0            # Index of the current (lookahead) token
        self.metrics = Metrics()  # Metric collector shared across all rules

    # ------------------------------------------------------------------
    #  Utility helpers
    # ------------------------------------------------------------------

    def current(self):
        """Return the current lookahead token without consuming it."""
        return self.tokens[self.pos]

    def consume(self, expected_type: str):
        """
        Verify the current token matches *expected_type*, advance the
        position, increment the token counter, and return the token.

        Raises:
            SyntaxError: if the current token type does not match.
        """
        token = self.current()
        if token.type != expected_type:
            raise SyntaxError(
                f"[Parser] Expected '{expected_type}' "
                f"but got '{token.type}' (value={token.value!r}) "
                f"at token index {self.pos}"
            )
        self.pos += 1
        self.metrics.token_count += 1  # Count every successfully consumed token
        return token

    # ------------------------------------------------------------------
    #  Entry point
    # ------------------------------------------------------------------

    def parse(self) -> TreeNode:
        """
        Parse the entire token stream.

        Returns the root TreeNode of the parse tree.
        Raises SyntaxError if tokens remain after the program ends.
        """
        root = self.parse_program(depth=0)

        # After a valid program, the only remaining token should be EOF
        if self.current().type != 'EOF':
            raise SyntaxError(
                f"[Parser] Unexpected token after program end: {self.current()}"
            )
        return root

    # ------------------------------------------------------------------
    #  Grammar rule methods  (one method per non-terminal)
    # ------------------------------------------------------------------

    def parse_program(self, depth: int) -> TreeNode:
        """
        Program → StatementList

        The top-level rule. Every valid program is a list of statements.
        """
        self.metrics.record_rule('Program', depth)
        node = TreeNode('Program')
        node.add_child(self.parse_statement_list(depth + 1))
        return node

    def parse_statement_list(self, depth: int) -> TreeNode:
        """
        StatementList → Statement StatementList | ε

        Recursively matches zero or more statements.
        Terminates (ε) when the current token cannot start a Statement.
        """
        self.metrics.record_rule('StatementList', depth)
        node = TreeNode('StatementList')

        # FIRST(Statement) = { ID, PRINT }
        if self.current().type in ('ID', 'PRINT'):
            node.add_child(self.parse_statement(depth + 1))
            node.add_child(self.parse_statement_list(depth + 1))  # tail recursion
        # else: ε production – node stays childless (empty list)

        return node

    def parse_statement(self, depth: int) -> TreeNode:
        """
        Statement → Assignment | Print

        Uses the lookahead token to decide which alternative to expand.
        """
        self.metrics.record_rule('Statement', depth)
        node = TreeNode('Statement')

        if self.current().type == 'ID':
            # Starts with an identifier → must be an Assignment
            node.add_child(self.parse_assignment(depth + 1))
        elif self.current().type == 'PRINT':
            # Starts with 'print' keyword → must be a Print
            node.add_child(self.parse_print(depth + 1))
        else:
            raise SyntaxError(
                f"[Parser] Statement expected ID or 'print', "
                f"got '{self.current().type}' ({self.current().value!r})"
            )
        return node

    def parse_assignment(self, depth: int) -> TreeNode:
        """
        Assignment → id = Expr ;

        Matches:  <identifier>  =  <expression>  ;
        """
        self.metrics.record_rule('Assignment', depth)
        node = TreeNode('Assignment')

        id_token = self.consume('ID')
        node.add_child(TreeNode(f'id:{id_token.value}'))   # terminal leaf

        self.consume('ASSIGN')
        node.add_child(TreeNode('='))                       # terminal leaf

        node.add_child(self.parse_expr(depth + 1))          # non-terminal

        self.consume('SEMI')
        node.add_child(TreeNode(';'))                       # terminal leaf

        return node

    def parse_print(self, depth: int) -> TreeNode:
        """
        Print → print ( Expr ) ;

        Matches:  print  (  <expression>  )  ;
        """
        self.metrics.record_rule('Print', depth)
        node = TreeNode('Print')

        self.consume('PRINT')
        node.add_child(TreeNode('print'))   # terminal leaf

        self.consume('LPAREN')
        node.add_child(TreeNode('('))       # terminal leaf

        node.add_child(self.parse_expr(depth + 1))

        self.consume('RPAREN')
        node.add_child(TreeNode(')'))       # terminal leaf

        self.consume('SEMI')
        node.add_child(TreeNode(';'))       # terminal leaf

        return node

    def parse_expr(self, depth: int) -> TreeNode:
        """
        Expr → Term ExprRest

        An expression is a Term followed by an optional tail of '+ Term' pairs.
        """
        self.metrics.record_rule('Expr', depth)
        node = TreeNode('Expr')
        node.add_child(self.parse_term(depth + 1))
        node.add_child(self.parse_expr_rest(depth + 1))
        return node

    def parse_expr_rest(self, depth: int) -> TreeNode:
        """
        ExprRest → + Term ExprRest | ε

        Handles right-recursive addition.
        ε branch fires when the current token is not '+'.
        """
        self.metrics.record_rule('ExprRest', depth)
        node = TreeNode('ExprRest')

        if self.current().type == 'PLUS':
            self.consume('PLUS')
            node.add_child(TreeNode('+'))                       # terminal leaf
            node.add_child(self.parse_term(depth + 1))
            node.add_child(self.parse_expr_rest(depth + 1))    # tail recursion
        # else: ε – no children

        return node

    def parse_term(self, depth: int) -> TreeNode:
        """
        Term → Factor TermRest

        A term is a Factor followed by an optional tail of '* Factor' pairs.
        """
        self.metrics.record_rule('Term', depth)
        node = TreeNode('Term')
        node.add_child(self.parse_factor(depth + 1))
        node.add_child(self.parse_term_rest(depth + 1))
        return node

    def parse_term_rest(self, depth: int) -> TreeNode:
        """
        TermRest → * Factor TermRest | ε

        Handles right-recursive multiplication.
        ε branch fires when the current token is not '*'.
        """
        self.metrics.record_rule('TermRest', depth)
        node = TreeNode('TermRest')

        if self.current().type == 'STAR':
            self.consume('STAR')
            node.add_child(TreeNode('*'))                       # terminal leaf
            node.add_child(self.parse_factor(depth + 1))
            node.add_child(self.parse_term_rest(depth + 1))    # tail recursion
        # else: ε – no children

        return node

    def parse_factor(self, depth: int) -> TreeNode:
        """
        Factor → ( Expr ) | id | number

        The base case of expression parsing.
        Either a parenthesized sub-expression, an identifier, or a number.
        """
        self.metrics.record_rule('Factor', depth)
        node = TreeNode('Factor')

        if self.current().type == 'LPAREN':
            # Parenthesized expression: ( Expr )
            self.consume('LPAREN')
            node.add_child(TreeNode('('))
            node.add_child(self.parse_expr(depth + 1))
            self.consume('RPAREN')
            node.add_child(TreeNode(')'))

        elif self.current().type == 'ID':
            # Identifier reference
            id_token = self.consume('ID')
            node.add_child(TreeNode(f'id:{id_token.value}'))

        elif self.current().type == 'NUMBER':
            # Numeric literal
            num_token = self.consume('NUMBER')
            node.add_child(TreeNode(f'num:{num_token.value}'))

        else:
            raise SyntaxError(
                f"[Parser] Factor expected '(', id, or number, "
                f"got '{self.current().type}' ({self.current().value!r})"
            )

        return node
