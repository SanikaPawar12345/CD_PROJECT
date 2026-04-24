from fastapi.testclient import TestClient

from api import app, _normalize_code_text, _optimize_basic_code


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_analyze_full_and_tokens_mode():
    payload = {"code": "x = 1 + 2;\nprint(x);", "analysis_level": "full", "visualization": True}
    response = client.post("/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "token_type_count" in data
    assert "rule_breakdown" in data
    assert "cost_breakdown" in data

    tokens_only = client.post("/analyze", json={"code": "x = 1;", "analysis_level": "tokens"})
    assert tokens_only.status_code == 200
    assert tokens_only.json()["rule_count"] == 0


def test_analyze_accepts_subtraction_expression():
    payload = {
        "code": "x = 3 + 4 * 2;\ny = x + 1;\nz = (x + y) * (y - 2);\nprint(z);",
        "analysis_level": "full",
    }
    response = client.post("/analyze", json=payload)
    assert response.status_code == 200


def test_local_optimizer_simplifies_basic_expression_chain():
    source = "\n".join([
        "x = 3 + 4 * 2;",
        "y = x + 1;",
        "z = (x + y) * (y - 2);",
        "a = z + x * 2 + y * 3;",
        "b = a + a * 0 + (x * 1);",
        "print(b);",
    ])

    optimized, notes = _optimize_basic_code(source)

    assert _normalize_code_text(optimized) != _normalize_code_text(source)
    assert "b = a + x;" in optimized
    assert notes


def test_local_optimizer_no_change_for_already_optimized_code():
    source = "x = 11;\ny = x + 1;\nprint(y);"
    optimized, notes = _optimize_basic_code(source)

    assert _normalize_code_text(optimized) == _normalize_code_text(source)
    assert notes == []


def test_validate_syntax_endpoint():
    ok_response = client.post("/validate-syntax", json={"source_code": "x = 1;"})
    assert ok_response.status_code == 200
    assert ok_response.json()["valid"] is True

    bad_response = client.post("/validate-syntax", json={"source_code": "x = ;"})
    assert bad_response.status_code == 422
    detail = bad_response.json()["detail"]
    assert "line" in detail
    assert "column" in detail


def test_analyze_full_c_grammar_pipeline_output_consistency():
    payload = {
        "code": 'int x = 3 + 4 * 2;\nprintf("%d", x);',
        "analysis_level": "full",
        "grammar": "c",
    }
    response = client.post("/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["grammar"] == "c"
    assert isinstance(data["tokens"], list)
    assert data["parse_tree"] is not None
    assert data["token_count"] > 0
    assert data["rule_count"] > 0
    assert data["max_depth"] > 0
    assert data["cost_score"] > 0
    assert isinstance(data["suggestions"], list)


def test_analyze_full_regex_grammar_pipeline_output_consistency():
    payload = {
        "code": "(a|b)*abb",
        "analysis_level": "full",
        "grammar": "regex",
    }
    response = client.post("/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["grammar"] == "regex"
    assert isinstance(data["tokens"], list)
    assert data["parse_tree"] is not None
    assert data["token_count"] > 0
    assert data["rule_count"] > 0
    assert data["max_depth"] > 0
    assert data["cost_score"] > 0
    assert isinstance(data["suggestions"], list)


def test_grammar_aliases_remain_backward_compatible():
    payload = {
        "code": "x = 1 + 2;",
        "analysis_level": "syntax",
        "grammar": "strict-v1",
    }
    response = client.post("/analyze", json=payload)
    assert response.status_code == 200
    assert response.json()["grammar"] == "default"


def test_analyze_rejects_c_input_for_default_grammar():
    payload = {
        "code": 'int x = 5;\nprintf("%d", x);',
        "analysis_level": "full",
        "grammar": "default",
    }
    response = client.post("/analyze", json=payload)
    assert response.status_code == 400
    assert "Invalid input for selected grammar" in response.json()["detail"]["message"]


def test_validate_syntax_rejects_expression_input_for_c_grammar():
    payload = {
        "source_code": "x = 1 + 2;\nprint(x);",
        "grammar": "c",
    }
    response = client.post("/validate-syntax", json=payload)
    assert response.status_code == 400
    assert "Expected C code" in response.json()["detail"]["message"]


def test_parse_tree_diff_rejects_multiline_for_regex_grammar():
    payload = {
        "source_a": "(a|b)*abb\n(a|b)",
        "source_b": "(a|b)+abb",
        "grammar": "regex",
    }
    response = client.post("/parse-tree-diff", json=payload)
    assert response.status_code == 400
    assert "single-line pattern" in response.json()["detail"]["message"]
