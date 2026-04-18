import re

from src.lexer import Token, tokenize
from src.parser import Parser, CLikeParser
from src.grammars.base import GrammarInfo


def c_like_tokenize(source_code: str) -> list[Token]:
    TOKEN_SPEC = [
        ('STRING',   r'"(?:[^"\\]|\\.)*"'),
        ('INT',      r'\bint\b'),
        ('PRINTF',   r'\bprintf\b'),
        ('NUMBER',   r'\d+(\.\d*)?'),
        ('ID',       r'[a-zA-Z_]\w*'),
        ('ASSIGN',   r'='),
        ('PLUS',     r'\+'),
        ('STAR',     r'\*'),
        ('LPAREN',   r'\('),
        ('RPAREN',   r'\)'),
        ('SEMI',     r';'),
        ('COMMA',    r','),
        ('SKIP',     r'[ \t\n\r]+'),
        ('COMMENT',  r'//[^\n]*'),
        ('MISMATCH', r'.'),
    ]

    master_re = re.compile(
        '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPEC)
    )

    tokens: list[Token] = []
    line_starts = [0]
    for idx, ch in enumerate(source_code):
        if ch == '\n':
            line_starts.append(idx + 1)

    def get_line_col(pos: int) -> tuple[int, int]:
        line = 1
        for i, start in enumerate(line_starts, start=1):
            if start > pos:
                break
            line = i
        column = (pos - line_starts[line - 1]) + 1
        return line, column

    for match in master_re.finditer(source_code):
        kind = match.lastgroup
        value = match.group()
        start_pos = match.start()
        line, column = get_line_col(start_pos)

        if kind in ('SKIP', 'COMMENT'):
            continue
        elif kind == 'MISMATCH':
            raise SyntaxError(
                f"[Lexer] Unexpected character: {value!r} "
                f"at line {line}, column {column}"
            )

        tokens.append(Token(kind, value, line=line, column=column, position=start_pos))

    eof_line, eof_col = get_line_col(len(source_code)) if source_code else (1, 1)
    tokens.append(Token('EOF', '', line=eof_line, column=eof_col, position=len(source_code)))
    return tokens


def regex_tokenize(source_code: str) -> list[Token]:
    """Tokenizer for regex grammar input.

    Recognizes the same basic expression tokens plus slash-delimited regex literals.
    """
    TOKEN_SPEC = [
        ('REGEX',    r'/([^\\/]|\\.)+?/'),
        ('NUMBER',   r'\d+(\.\d*)?'),
        ('ID',       r'[a-zA-Z_]\w*'),
        ('ASSIGN',   r'='),
        ('PLUS',     r'\+'),
        ('STAR',     r'\*'),
        ('LPAREN',   r'\('),
        ('RPAREN',   r'\)'),
        ('SEMI',     r';'),
        ('SKIP',     r'[ \t\n\r]+'),
        ('COMMENT',  r'#[^\n]*'),
        ('MISMATCH', r'.'),
    ]

    master_re = re.compile(
        '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPEC)
    )

    tokens: list[Token] = []
    line_starts = [0]
    for idx, ch in enumerate(source_code):
        if ch == '\n':
            line_starts.append(idx + 1)

    def get_line_col(pos: int) -> tuple[int, int]:
        line = 1
        for i, start in enumerate(line_starts, start=1):
            if start > pos:
                break
            line = i
        column = (pos - line_starts[line - 1]) + 1
        return line, column

    for match in master_re.finditer(source_code):
        kind = match.lastgroup
        value = match.group()
        start_pos = match.start()
        line, column = get_line_col(start_pos)

        if kind in ('SKIP', 'COMMENT'):
            continue
        elif kind == 'MISMATCH':
            raise SyntaxError(
                f"[Lexer] Unexpected character: {value!r} "
                f"at line {line}, column {column}"
            )
        elif kind == 'ID' and value == 'print':
            kind = 'PRINT'

        tokens.append(Token(kind, value, line=line, column=column, position=start_pos))

    eof_line, eof_col = get_line_col(len(source_code)) if source_code else (1, 1)
    tokens.append(Token('EOF', '', line=eof_line, column=eof_col, position=len(source_code)))
    return tokens


class DefaultExpressionGrammar:
    key = "default"
    name = "Expression Grammar v1"
    description = "Assignment/print expression grammar implemented with recursive descent."
    rules = [
        "Program -> StatementList",
        "StatementList -> Statement StatementList | ε",
        "Statement -> Assignment | Print",
        "Assignment -> id = Expr ;",
        "Print -> print ( Expr ) ;",
        "Expr -> Term ExprRest",
        "ExprRest -> (+ | -) Term ExprRest | ε",
        "Term -> Factor TermRest",
        "TermRest -> * Factor TermRest | ε",
        "Factor -> ( Expr ) | id | number",
    ]

    def tokenize(self, source: str):
        return tokenize(source)

    def parse_with_metrics(self, tokens):
        parser = Parser(tokens)
        tree = parser.parse()
        return tree, parser.metrics.summary()

    def info(self) -> GrammarInfo:
        return GrammarInfo(key=self.key, name=self.name, description=self.description, rules=self.rules)


class StrictExpressionGrammar(DefaultExpressionGrammar):
    key = "strict-v1"
    name = "Strict Expression Grammar v1"
    description = "Same core grammar with strict mode identity; reserved for grammar-specific extensions."


class CLikeExpressionGrammar(DefaultExpressionGrammar):
    key = "c-subset-v1"
    name = "C-like Subset Grammar v1"
    description = "Minimal C-style subset with int declarations and printf statements."
    rules = [
        "Program -> StatementList",
        "StatementList -> Statement StatementList | ε",
        "Statement -> Declaration | Assignment | Print | Printf",
        "Declaration -> int id = Expr ; | int id ;",
        "Assignment -> id = Expr ;",
        "Print -> print ( Expr ) ;",
        "Printf -> printf ( STRING , Expr ) ;",
        "Expr -> Term ExprRest",
        "ExprRest -> (+ | -) Term ExprRest | ε",
        "Term -> Factor TermRest",
        "TermRest -> * Factor TermRest | ε",
        "Factor -> ( Expr ) | id | number",
    ]

    def tokenize(self, source: str):
        return c_like_tokenize(source)

    def parse_with_metrics(self, tokens):
        parser = CLikeParser(tokens)
        tree = parser.parse()
        return tree, parser.metrics.summary()


class RegexExpressionGrammar(DefaultExpressionGrammar):
    key = "regex-v1"
    name = "Regex Grammar v1"
    description = "Expression grammar extended with slash-delimited regex literals like /abc[0-9]+/."
    rules = [
        "Program -> StatementList",
        "StatementList -> Statement StatementList | ε",
        "Statement -> Assignment | Print",
        "Assignment -> id = Expr ;",
        "Print -> print ( Expr ) ;",
        "Expr -> Term ExprRest",
        "ExprRest -> + Term ExprRest | ε",
        "Term -> Factor TermRest",
        "TermRest -> * Factor TermRest | ε",
        "Factor -> ( Expr ) | id | number | regex",
        "RegexLiteral -> /.../",
    ]

    def tokenize(self, source: str):
        return regex_tokenize(source)

    def parse_with_metrics(self, tokens):
        parser = Parser(tokens)
        tree = parser.parse()
        return tree, parser.metrics.summary()
