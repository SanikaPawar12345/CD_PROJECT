from pathlib import Path
content = '''# parser.py
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
    """Recursive Descent Parser.

    Usage:
        parser = Parser(tokens)       # tokens from lexer.tokenize()
        tree   = parser.parse()       # returns root TreeNode
        report = parser.metrics.summary()
    """

    def __init__(self, tokens: list):
        self.tokens = tokens
        self.pos = 0
        self.metrics = Metrics()

    def current(self):
        return self.tokens[self.pos]

    def consume(self, expected_type: str):
        token = self.current()
        if token.type != expected_type:
            raise SyntaxError(
                f"[Parser] Expected '{expected_type}' "
                f"but got '{token.type}' (value={token.value!r}) "
                f"at line {getattr(token, 'line', '?')}, column {getattr(token, 'column', '?')} "
                f"(token index {self.pos})"
            )
        self.pos += 1
        self.metrics.token_count += 1
        return token

    def parse(self) -> TreeNode:
        root = self.parse_program(depth=0)
        if self.current().type != 'EOF':
            token = self.current()
            raise SyntaxError(
                f"[Parser] Unexpected token after program end: {token} "
                f"at line {getattr(token, 'line', '?')}, column {getattr(token, 'column', '?')}"
            )
        return root

    def parse_program(self, depth: int) -> TreeNode:
        self.metrics.record_rule('Program', depth)
        node = TreeNode('Program')
        node.add_child(self.parse_statement_list(depth + 1))
        return node

    def parse_statement_list(self, depth: int) -> TreeNode:
        self.metrics.record_rule('StatementList', depth)
        node = TreeNode('StatementList')
        if self.current().type in ('ID', 'PRINT'):
            node.add_child(self.parse_statement(depth + 1))
            node.add_child(self.parse_statement_list(depth + 1))
        return node

    def parse_statement(self, depth: int) -> TreeNode:
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
        self.metrics.record_rule('Assignment', depth)
        node = TreeNode('Assignment')
        id_token = self.consume('ID')
        node.add_child(TreeNode(f'id:{id_token.value}'))
        self.consume('ASSIGN')
        node.add_child(TreeNode('='))
        node.add_child(self.parse_expr(depth + 1))
        self.consume('SEMI')
        node.add_child(TreeNode(';'))
        return node

    def parse_print(self, depth: int) -> TreeNode:
        self.metrics.record_rule('Print', depth)
        node = TreeNode('Print')
        self.consume('PRINT')
        node.add_child(TreeNode('print'))
        self.consume('LPAREN')
        node.add_child(TreeNode('('))
        node.add_child(self.parse_expr(depth + 1))
        self.consume('RPAREN')
        node.add_child(TreeNode(')'))
        self.consume('SEMI')
        node.add_child(TreeNode(';'))
        return node

    def parse_expr(self, depth: int) -> TreeNode:
        self.metrics.record_rule('Expr', depth)
        node = TreeNode('Expr')
        node.add_child(self.parse_term(depth + 1))
        node.add_child(self.parse_expr_rest(depth + 1))
        return node

    def parse_expr_rest(self, depth: int) -> TreeNode:
        self.metrics.record_rule('ExprRest', depth)
        node = TreeNode('ExprRest')
        if self.current().type == 'PLUS':
            self.consume('PLUS')
            node.add_child(TreeNode('+'))
            node.add_child(self.parse_term(depth + 1))
            node.add_child(self.parse_expr_rest(depth + 1))
        return node

    def parse_term(self, depth: int) -> TreeNode:
        self.metrics.record_rule('Term', depth)
        node = TreeNode('Term')
        node.add_child(self.parse_factor(depth + 1))
        node.add_child(self.parse_term_rest(depth + 1))
        return node

    def parse_term_rest(self, depth: int) -> TreeNode:
        self.metrics.record_rule('TermRest', depth)
        node = TreeNode('TermRest')
        if self.current().type == 'STAR':
            self.consume('STAR')
            node.add_child(TreeNode('*'))
            node.add_child(self.parse_factor(depth + 1))
            node.add_child(self.parse_term_rest(depth + 1))
        return node

    def parse_factor(self, depth: int) -> TreeNode:
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
                f"[Parser] Factor expected '(', id, number, or regex, "
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
        if self.current().type in ('ID', 'PRINT', 'INT', 'PRINTF'):
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
        elif self.current().type == 'ID':
            node.add_child(self.parse_assignment(depth + 1))
        elif self.current().type == 'PRINT':
            node.add_child(self.parse_print(depth + 1))
        else:
            token = self.current()
            raise SyntaxError(
                f"[Parser] Statement expected INT, ID, PRINT, or PRINTF, "
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
'''
Path('src/parser.py').write_text(content, encoding='utf-8')
