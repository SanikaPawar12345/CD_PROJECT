from fastapi.testclient import TestClient

from api import app


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


def test_validate_syntax_endpoint():
    ok_response = client.post("/validate-syntax", json={"source_code": "x = 1;"})
    assert ok_response.status_code == 200
    assert ok_response.json()["valid"] is True

    bad_response = client.post("/validate-syntax", json={"source_code": "x = ;"})
    assert bad_response.status_code == 422
    detail = bad_response.json()["detail"]
    assert "line" in detail
    assert "column" in detail
