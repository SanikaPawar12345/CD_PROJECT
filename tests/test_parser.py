import pytest

from src.grammars import get_grammar
from src.lexer import tokenize
from src.parser import Parser


def test_parser_builds_program_tree():
    parser = Parser(tokenize("x = 1 + 2;\nprint(x);"))
    tree = parser.parse()

    assert tree.label == "Program"
    summary = parser.metrics.summary()
    assert summary["token_count"] > 0
    assert summary["total_rule_applications"] > 0


def test_parser_accepts_subtraction_in_expression():
    parser = Parser(tokenize("x = (3 + 4) * (5 - 2);\nprint(x);"))
    tree = parser.parse()
    assert tree.label == "Program"


def test_parser_error_contains_line_column():
    parser = Parser(tokenize("x = ;"))

    with pytest.raises(SyntaxError) as exc:
        parser.parse()

    message = str(exc.value)
    assert "line" in message
    assert "column" in message


def test_regex_grammar_parses_regex_literal():
    grammar = get_grammar('regex-v1')
    tokens = grammar.tokenize("x = /foo[0-9]+/;")

    assert any(token.type == 'REGEX' for token in tokens)

    parser = Parser(tokens)
    tree = parser.parse()
    summary = parser.metrics.summary()

    assert tree.label == 'Program'
    assert summary['total_rule_applications'] > 0


def test_c_like_grammar_parses_declaration_and_printf():
    grammar = get_grammar('c-subset-v1')
    tokens = grammar.tokenize('int x = 3 + 4; printf("x=%d", x);')

    assert any(token.type == 'INT' for token in tokens)
    assert any(token.type == 'PRINTF' for token in tokens)
    assert any(token.type == 'STRING' for token in tokens)

    tree, summary = grammar.parse_with_metrics(tokens)

    assert tree.label == 'Program'
    assert summary['total_rule_applications'] > 0
