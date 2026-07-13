"""End-to-end test of POST /graph/validate. No external services involved —
step 5 is pure networkx logic, so no fakes/dependency overrides are needed."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_validate_endpoint_breaks_a_cycle_and_reports_the_drop():
    payload = {
        "edges": [
            {"from": "a", "to": "b", "confidence": 0.9},
            {"from": "b", "to": "a", "confidence": 0.1},
        ]
    }

    response = client.post("/graph/validate", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["edges"] == [{"from": "a", "to": "b", "confidence": 0.9}]
    assert body["dropped_edges"][0]["from"] == "b"
    assert body["dropped_edges"][0]["to"] == "a"
