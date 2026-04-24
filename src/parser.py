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
#   ExprRest → (+ | -) Term ExprRest | ε
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
#   ExprRest      → (+ | -) Term ExprRest | ε
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
                f"at line {getattr(token, 'line', '?')}, column {getattr(token, 'column', '?')} "
                f"(token index {self.pos})"
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
            token = self.current()
            raise SyntaxError(
                f"[Parser] Unexpected token after program end: {token} "
                f"at line {getattr(token, 'line', '?')}, column {getattr(token, 'column', '?')}"
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
            node.add_child(self.parse_assignment(depth + 1))
        elif self.current().type == 'PRINT':
            node.add_child(self.parse_print(depth + 1))
        else:
            token = self.current()
            raise SyntaxError(
                f"[Parser] Statement expected ID or 'print', "
                f"got '{token.type}' ({token.value!r}) "
                f"at line {getattr(token, 'line', '?')}, column {getattr(token, 'column', '?')}"
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
        ExprRest → (+ | -) Term ExprRest | ε

        Handles right-recursive addition/subtraction.
        ε branch fires when the current token is neither '+' nor '-'.
        """
        self.metrics.record_rule('ExprRest', depth)
        node = TreeNode('ExprRest')

        if self.current().type in ('PLUS', 'MINUS'):
            op_token = self.current()
            self.consume(op_token.type)
            node.add_child(TreeNode(op_token.value))            # terminal leaf
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
        TermRest → (* | /) Factor TermRest | ε

        Handles right-recursive multiplication/division.
        ε branch fires when the current token is neither '*' nor '/'.
        """
        self.metrics.record_rule('TermRest', depth)
        node = TreeNode('TermRest')

        if self.current().type in ('STAR', 'SLASH'):
            op_token = self.current()
            self.consume(op_token.type)
            node.add_child(TreeNode(op_token.value))            # terminal leaf
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
            self.consume('LPAREN')
            node.add_child(TreeNode('('))
            node.add_child(self.parse_expr(depth + 1))
            self.consume('RPAREN')
            node.add_child(TreeNode(')'))

        elif self.current().type == 'ID':
            id_token = self.consume('ID')
            node.add_child(TreeNode(f'id:{id_token.value}'))

        elif self.current().type == 'NUMBER':
            num_token = self.consume('NUMBER')
            node.add_child(TreeNode(f'num:{num_token.value}'))

        elif self.current().type == 'REGEX':
            regex_token = self.consume('REGEX')
            node.add_child(TreeNode(f'regex:{regex_token.value}'))

        else:
            token = self.current()
            raise SyntaxError(
                f"[Parser] Factor expected '(', id, or number, "
                f"got '{token.type}' ({token.value!r}) "
                f"at line {getattr(token, 'line', '?')}, column {getattr(token, 'column', '?')}"
            )

        return node


class CLikeParser(Parser):
    """Parser for a minimal C-like subset.

    Supports:
      - int declarations: int x = Expr ;
      - assignments: x = Expr ;
      - printf calls: printf("text", Expr) ;
      - arithmetic expressions with +, * and parenthesis.
    """

    def parse_statement_list(self, depth: int) -> TreeNode:
        self.metrics.record_rule('StatementList', depth)
        node = TreeNode('StatementList')
        if self.current().type in ('ID', 'PRINT', 'INT', 'PRINTF', 'RETURN'):
            node.add_child(self.parse_statement(depth + 1))
            node.add_child(self.parse_statement_list(depth + 1))
        return node

    def parse_statement(self, depth: int) -> TreeNode:
        self.metrics.record_rule('Statement', depth)
        node = TreeNode('Statement')

        if self.current().type == 'INT':
            node.add_child(self.parse_declaration(depth + 1))
        elif self.current().type == 'PRINTF':
            node.add_child(self.parse_printf(depth + 1))
        elif self.current().type == 'RETURN':
            node.add_child(self.parse_return(depth + 1))
        elif self.current().type == 'ID':
            node.add_child(self.parse_assignment(depth + 1))
        elif self.current().type == 'PRINT':
            node.add_child(self.parse_print(depth + 1))
        else:
            token = self.current()
            raise SyntaxError(
                f"[Parser] Statement expected INT, ID, PRINT, PRINTF, or RETURN, "
                f"got '{token.type}' ({token.value!r}) "
                f"at line {getattr(token, 'line', '?')}, column {getattr(token, 'column', '?')}"
            )
        return node

    def parse_declaration(self, depth: int) -> TreeNode:
        self.metrics.record_rule('Declaration', depth)
        node = TreeNode('Declaration')

        self.consume('INT')
        node.add_child(TreeNode('int'))

        id_token = self.consume('ID')
        node.add_child(TreeNode(f'id:{id_token.value}'))

        if self.current().type == 'ASSIGN':
            self.consume('ASSIGN')
            node.add_child(TreeNode('='))
            node.add_child(self.parse_expr(depth + 1))

        self.consume('SEMI')
        node.add_child(TreeNode(';'))
        return node

    def parse_printf(self, depth: int) -> TreeNode:
        self.metrics.record_rule('Printf', depth)
        node = TreeNode('Printf')

        self.consume('PRINTF')
        node.add_child(TreeNode('printf'))

        self.consume('LPAREN')
        node.add_child(TreeNode('('))

        string_token = self.consume('STRING')
        node.add_child(TreeNode(f'str:{string_token.value}'))

        self.consume('COMMA')
        node.add_child(TreeNode(','))

        node.add_child(self.parse_expr(depth + 1))

        self.consume('RPAREN')
        node.add_child(TreeNode(')'))
        self.consume('SEMI')
        node.add_child(TreeNode(';'))

        return node

    def parse_return(self, depth: int) -> TreeNode:
        self.metrics.record_rule('Return', depth)
        node = TreeNode('Return')

        self.consume('RETURN')
        node.add_child(TreeNode('return'))

        node.add_child(self.parse_expr(depth + 1))

        self.consume('SEMI')
        node.add_child(TreeNode(';'))
        return node


class RegexParser(Parser):
    """Parser for regex expressions.

    Grammar:
      Program    -> RegexExpr
      RegexExpr  -> Union
      Union      -> Concat UnionRest
      UnionRest  -> | Concat UnionRest | ε
      Concat     -> Repeat Concat | Repeat
      Repeat     -> Primary Quantifier*
      Quantifier -> * | + | ?
      Primary    -> ( RegexExpr ) | literal
    """

    def parse_program(self, depth: int) -> TreeNode:
        self.metrics.record_rule('Program', depth)
        node = TreeNode('Program')
        node.add_child(self.parse_regex_expr(depth + 1))
        return node

    def parse_regex_expr(self, depth: int) -> TreeNode:
        self.metrics.record_rule('RegexExpr', depth)
        node = TreeNode('RegexExpr')
        node.add_child(self.parse_union(depth + 1))
        return node

    def parse_union(self, depth: int) -> TreeNode:
        self.metrics.record_rule('Union', depth)
        node = TreeNode('Union')
        node.add_child(self.parse_concat(depth + 1))
        node.add_child(self.parse_union_rest(depth + 1))
        return node

    def parse_union_rest(self, depth: int) -> TreeNode:
        self.metrics.record_rule('UnionRest', depth)
        node = TreeNode('UnionRest')
        if self.current().type == 'ALT':
            self.consume('ALT')
            node.add_child(TreeNode('|'))
            node.add_child(self.parse_concat(depth + 1))
            node.add_child(self.parse_union_rest(depth + 1))
        return node

    def parse_concat(self, depth: int) -> TreeNode:
        self.metrics.record_rule('Concat', depth)
        node = TreeNode('Concat')
        node.add_child(self.parse_repeat(depth + 1))

        while self.current().type in ('LITERAL', 'LPAREN'):
            node.add_child(self.parse_repeat(depth + 1))

        return node

    def parse_repeat(self, depth: int) -> TreeNode:
        self.metrics.record_rule('Repeat', depth)
        node = TreeNode('Repeat')
        node.add_child(self.parse_primary(depth + 1))

        while self.current().type in ('STAR', 'PLUS', 'QMARK'):
            quant = self.current()
            self.consume(quant.type)
            node.add_child(TreeNode(quant.value))

        return node

    def parse_primary(self, depth: int) -> TreeNode:
        self.metrics.record_rule('Primary', depth)
        node = TreeNode('Primary')

        if self.current().type == 'LPAREN':
            self.consume('LPAREN')
            node.add_child(TreeNode('('))
            node.add_child(self.parse_regex_expr(depth + 1))
            self.consume('RPAREN')
            node.add_child(TreeNode(')'))
            return node

        if self.current().type == 'LITERAL':
            token = self.consume('LITERAL')
            node.add_child(TreeNode(f'literal:{token.value}'))
            return node

        token = self.current()
        raise SyntaxError(
            f"[Parser] Regex primary expected literal or '(', "
            f"got '{token.type}' ({token.value!r}) "
            f"at line {getattr(token, 'line', '?')}, column {getattr(token, 'column', '?')}"
        )

