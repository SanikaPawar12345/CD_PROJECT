from src.lexer import tokenize
from src.parser import Parser
from src.grammars.base import GrammarInfo


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
        "ExprRest -> + Term ExprRest | ε",
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
