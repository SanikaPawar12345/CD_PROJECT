import re

from src.grammars.base import GrammarInfo
from src.lexer import Token
from src.parser import CLikeParser


C_TOKEN_SPEC = [
    ('STRING',   r'"(?:[^"\\]|\\.)*"'),
    ('INT',      r'\bint\b'),
    ('RETURN',   r'\breturn\b'),
    ('PRINTF',   r'\bprintf\b'),
    ('NUMBER',   r'\d+'),
    ('ID',       r'[a-zA-Z_]\w*'),
    ('ASSIGN',   r'='),
    ('PLUS',     r'\+'),
    ('MINUS',    r'-'),
    ('STAR',     r'\*'),
    ('SLASH',    r'/'),
    ('LPAREN',   r'\('),
    ('RPAREN',   r'\)'),
    ('LBRACE',   r'\{'),
    ('RBRACE',   r'\}'),
    ('SEMI',     r';'),
    ('COMMA',    r','),
    ('SKIP',     r'[ \t\n\r]+'),
    ('COMMENT',  r'//[^\n]*'),
    ('MISMATCH', r'.'),
]


def c_tokenize(source_code: str) -> list[Token]:
    master_re = re.compile('|'.join(f'(?P<{name}>{pattern})' for name, pattern in C_TOKEN_SPEC))

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
        if kind == 'MISMATCH':
            raise SyntaxError(
                f"[Lexer] Unexpected character: {value!r} "
                f"at line {line}, column {column}"
            )

        tokens.append(Token(kind, value, line=line, column=column, position=start_pos))

    eof_line, eof_col = get_line_col(len(source_code)) if source_code else (1, 1)
    tokens.append(Token('EOF', '', line=eof_line, column=eof_col, position=len(source_code)))
    return tokens


class CGrammar:
    key = "c"
    name = "C Subset Grammar"
    description = "Basic C subset supporting declarations, assignments, arithmetic, and printf calls."
    rules = [
        "Program -> StatementList",
        "StatementList -> Statement StatementList | ε",
        "Statement -> Declaration | Assignment | Printf | Return",
        "Declaration -> int id = Expr ; | int id ;",
        "Assignment -> id = Expr ;",
        "Printf -> printf ( STRING , Expr ) ;",
        "Return -> return Expr ;",
        "Expr -> Term ExprRest",
        "ExprRest -> (+ | -) Term ExprRest | ε",
        "Term -> Factor TermRest",
        "TermRest -> (* | /) Factor TermRest | ε",
        "Factor -> ( Expr ) | id | number",
    ]

    def tokenize(self, source: str):
        return c_tokenize(source)

    def parse_with_metrics(self, tokens):
        parser = CLikeParser(tokens)
        tree = parser.parse()
        return tree, parser.metrics.summary()

    def info(self) -> GrammarInfo:
        return GrammarInfo(key=self.key, name=self.name, description=self.description, rules=self.rules)
