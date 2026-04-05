import pytest

from src.lexer import tokenize
from src.parser import Parser


def test_parser_builds_program_tree():
    parser = Parser(tokenize("x = 1 + 2;\nprint(x);"))
    tree = parser.parse()

    assert tree.label == "Program"
    summary = parser.metrics.summary()
    assert summary["token_count"] > 0
    assert summary["total_rule_applications"] > 0


def test_parser_error_contains_line_column():
    parser = Parser(tokenize("x = ;"))

    with pytest.raises(SyntaxError) as exc:
        parser.parse()

    message = str(exc.value)
    assert "line" in message
    assert "column" in message
