from src.lexer import tokenize


def test_tokenize_basic_program():
    tokens = tokenize("x = 3 + 4;\nprint(x);")
    visible = [t for t in tokens if t.type != "EOF"]

    assert [t.type for t in visible] == [
        "ID", "ASSIGN", "NUMBER", "PLUS", "NUMBER", "SEMI",
        "PRINT", "LPAREN", "ID", "RPAREN", "SEMI",
    ]
    assert visible[0].line == 1
    assert visible[0].column == 1


def test_tokenize_reports_line_column_on_invalid_char():
    try:
        tokenize("x = 1;\n@");
        assert False, "Expected SyntaxError"
    except SyntaxError as error:
        message = str(error)
        assert "line 2" in message
        assert "column 1" in message
