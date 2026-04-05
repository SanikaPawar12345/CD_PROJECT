# lexer.py
# Phase 1 – Lexical Analysis
#
# Converts raw source code text into a flat list of Token objects.
# Uses Python's built-in 're' module — no external lexer library needed.
#
# Supported tokens:
#   NUMBER   – integer or decimal literal (e.g. 42, 3.14)
#   ID       – identifier (e.g. x, result)
#   PRINT    – keyword 'print' (promoted from ID)
#   ASSIGN   – '='
#   PLUS     – '+'
#   STAR     – '*'
#   LPAREN   – '('
#   RPAREN   – ')'
#   SEMI     – ';'
#   EOF      – synthetic end-of-input marker

import re


# ---------------------------------------------------------------------------
# Token definition
# ---------------------------------------------------------------------------

class Token:
    """A single lexical unit with a type tag and its raw string value."""

    def __init__(self, type_: str, value: str, line: int = 1, column: int = 1, position: int = 0):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column
        self.position = position

    def __repr__(self) -> str:
        return f"Token({self.type}, {self.value!r})"


# ---------------------------------------------------------------------------
# Token specification table (order matters – more specific entries first)
# ---------------------------------------------------------------------------

# Each tuple: (token_type_name, regex_pattern)
TOKEN_SPEC = [
    ('NUMBER',   r'\d+(\.\d*)?'),    # Integer or decimal  e.g. 42, 3.14
    ('ID',       r'[a-zA-Z_]\w*'),   # Identifier          e.g. x, total
    ('ASSIGN',   r'='),              # Assignment operator
    ('PLUS',     r'\+'),             # Addition operator
    ('STAR',     r'\*'),             # Multiplication operator
    ('LPAREN',   r'\('),             # Left parenthesis
    ('RPAREN',   r'\)'),             # Right parenthesis
    ('SEMI',     r';'),              # Statement terminator
    ('SKIP',     r'[ \t\n\r]+'),     # Whitespace (ignored, not returned)
    ('COMMENT',  r'#[^\n]*'),        # Single-line comment  (ignored)
    ('MISMATCH', r'.'),              # Any other char → raises SyntaxError
]

# Combine all patterns into one master regex using named groups.
# Each group name is the token type.
MASTER_RE = re.compile(
    '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPEC)
)

# Keywords: identifiers that are reserved words in the language.
KEYWORDS = {'print'}


# ---------------------------------------------------------------------------
# Tokenizer function
# ---------------------------------------------------------------------------

def tokenize(source_code: str) -> list[Token]:
    """
    Scans *source_code* and returns a list of Token objects.

    Process:
      1. The master regex matches tokens left-to-right.
      2. SKIP (whitespace) and COMMENT tokens are discarded.
      3. If an ID matches a keyword, its type is upgraded (e.g. PRINT).
      4. MISMATCH raises a SyntaxError immediately.
      5. A synthetic EOF token is appended at the end.

    Args:
        source_code (str): The full program text to tokenize.

    Returns:
        list[Token]: Ordered list of tokens ending with Token('EOF', '').
    """
    tokens: list[Token] = []

    # Map absolute character positions to line/column for precise errors.
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

    for match in MASTER_RE.finditer(source_code):
        kind = match.lastgroup        # Which named group matched
        value = match.group()         # The matched text
        start_pos = match.start()
        line, column = get_line_col(start_pos)

        if kind in ('SKIP', 'COMMENT'):
            # Whitespace and comments are invisible to the parser
            continue

        elif kind == 'MISMATCH':
            raise SyntaxError(
                f"[Lexer] Unexpected character: {value!r} "
                f"at line {line}, column {column}"
            )

        elif kind == 'ID' and value in KEYWORDS:
            # Promote reserved word: 'print' → Token(PRINT, 'print')
            kind = value.upper()

        elif kind == 'NUMBER':
            # Strip the inner decimal group from the regex match group count;
            # value is already the full matched number string.
            pass

        tokens.append(Token(kind, value, line=line, column=column, position=start_pos))

    # Always end with EOF so the parser has a clean termination signal
    eof_line, eof_col = get_line_col(len(source_code)) if source_code else (1, 1)
    tokens.append(Token('EOF', '', line=eof_line, column=eof_col, position=len(source_code)))
    return tokens
