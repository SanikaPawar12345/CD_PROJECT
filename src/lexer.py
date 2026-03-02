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

    def __init__(self, type_: str, value: str):
        self.type = type_
        self.value = value

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

    for match in MASTER_RE.finditer(source_code):
        kind = match.lastgroup        # Which named group matched
        value = match.group()         # The matched text

        if kind in ('SKIP', 'COMMENT'):
            # Whitespace and comments are invisible to the parser
            continue

        elif kind == 'MISMATCH':
            raise SyntaxError(
                f"[Lexer] Unexpected character: {value!r} "
                f"at position {match.start()}"
            )

        elif kind == 'ID' and value in KEYWORDS:
            # Promote reserved word: 'print' → Token(PRINT, 'print')
            kind = value.upper()

        elif kind == 'NUMBER':
            # Strip the inner decimal group from the regex match group count;
            # value is already the full matched number string.
            pass

        tokens.append(Token(kind, value))

    # Always end with EOF so the parser has a clean termination signal
    tokens.append(Token('EOF', ''))
    return tokens
