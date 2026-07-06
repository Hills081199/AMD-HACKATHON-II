"""End-to-end test of POST /build-graph's wiring (step 4), with a fake
Fireworks client swapped in via FastAPI dependency overrides so no real
Fireworks API key or network access is required."""

from fastapi.testclient import TestClient

from worker.main import app, get_fireworks_client


class _FakeFireworks:
    def infer_direction(self, concept_a: dict, concept_b: dict) -> dict:
        return {"direction": "a_before_b", "confidence": 0.85}


def test_build_graph_endpoint_returns_candidate_edges():
    app.dependency_overrides[get_fireworks_client] = lambda: _FakeFireworks()
    try:
        client = TestClient(app)
        payload = {
            "concepts": [
                {"id": "concept_001", "name": "Derivatives", "definition": "...", "embedding": [1.0, 0.0]},
                {"id": "concept_002", "name": "Gradient descent", "definition": "...", "embedding": [0.99, 0.05]},
            ]
        }
        response = client.post("/build-graph", json=payload)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    edges = response.json()["edges"]
    assert edges == [{"from": "concept_001", "to": "concept_002", "confidence": 0.85}]
