"""End-to-end test of POST /embed's wiring (steps 2-3), with fakes swapped
in via FastAPI dependency overrides so no real Gemma server, network, or
sentence-transformers model download is required."""

import numpy as np
from fastapi.testclient import TestClient

from worker.concepts import RawConcept
from worker.main import app, get_embedder, get_gemma_extractor


class _FakeGemma:
    def extract(self, chunk):
        return [RawConcept(name=chunk.text, definition="stub", chunk_id=chunk.chunk_id)]


def _orthogonal_embed(texts: list[str]) -> np.ndarray:
    return np.eye(len(texts))


def test_embed_endpoint_returns_canonical_concepts():
    app.dependency_overrides[get_gemma_extractor] = lambda: _FakeGemma()
    app.dependency_overrides[get_embedder] = lambda: _orthogonal_embed
    try:
        client = TestClient(app)
        payload = {
            "chunks": [
                {"doc_id": "d.pdf", "chunk_id": "d.pdf:p1", "page": 1, "text": "Derivatives"},
                {"doc_id": "d.pdf", "chunk_id": "d.pdf:p2", "page": 2, "text": "Integrals"},
            ]
        }
        response = client.post("/embed", json=payload)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    concepts = response.json()["concepts"]
    assert {c["name"] for c in concepts} == {"Derivatives", "Integrals"}
    assert {tuple(c["chunk_ids"]) for c in concepts} == {("d.pdf:p1",), ("d.pdf:p2",)}
