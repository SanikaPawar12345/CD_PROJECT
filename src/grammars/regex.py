from src.grammars.base import GrammarInfo
from src.lexer import Token
from src.parser import RegexParser


def regex_tokenize(source_code: str) -> list[Token]:
    tokens: list[Token] = []
    line = 1
    column = 1
    pos = 0

    while pos < len(source_code):
        ch = source_code[pos]

        if ch in (' ', '\t', '\r'):
            pos += 1
            column += 1
            continue

        if ch == '\n':
            pos += 1
            line += 1
            column = 1
            continue

        if ch == '(':
            tokens.append(Token('LPAREN', ch, line=line, column=column, position=pos))
        elif ch == ')':
            tokens.append(Token('RPAREN', ch, line=line, column=column, position=pos))
        elif ch == '|':
            tokens.append(Token('ALT', ch, line=line, column=column, position=pos))
        elif ch == '*':
            tokens.append(Token('STAR', ch, line=line, column=column, position=pos))
        elif ch == '+':
            tokens.append(Token('PLUS', ch, line=line, column=column, position=pos))
        elif ch == '?':
            tokens.append(Token('QMARK', ch, line=line, column=column, position=pos))
        elif ch == '\\':
            if pos + 1 >= len(source_code):
                raise SyntaxError(f"[Lexer] Dangling escape at line {line}, column {column}")
            escaped = source_code[pos + 1]
            tokens.append(Token('LITERAL', escaped, line=line, column=column, position=pos))
            pos += 1
            column += 1
        elif ch in {'{', '}', '[', ']', '^', '$'}:
            raise SyntaxError(
                f"[Lexer] Unsupported regex token {ch!r} at line {line}, column {column}"
            )
        else:
            tokens.append(Token('LITERAL', ch, line=line, column=column, position=pos))

        pos += 1
        column += 1

    tokens.append(Token('EOF', '', line=line, column=column, position=pos))
    return tokens


class RegexGrammar:
    key = "regex"
    name = "Regex Grammar"
    description = "Regular expression grammar with alternation, grouping, and quantifiers."
    rules = [
        "Program -> RegexExpr",
        "RegexExpr -> Union",
        "Union -> Concat UnionRest",
        "UnionRest -> | Concat UnionRest | ε",
        "Concat -> Repeat Concat | Repeat",
        "Repeat -> Primary Quantifier*",
        "Quantifier -> * | + | ?",
        "Primary -> ( RegexExpr ) | literal",
    ]

    def tokenize(self, source: str):
        return regex_tokenize(source)

    def parse_with_metrics(self, tokens):
        parser = RegexParser(tokens)
        tree = parser.parse()
        return tree, parser.metrics.summary()

    def info(self) -> GrammarInfo:
        return GrammarInfo(key=self.key, name=self.name, description=self.description, rules=self.rules)
