"""Tests for pipeline steps 2-3 (docs/concept-graph-pipeline.md).

Uses fakes for both the Gemma client and the embedding model so the suite
never needs a real local Gemma server, network access, or a model download —
only worker/main.py's dependency-injected /embed endpoint touches the real
GemmaConceptExtractor/SentenceTransformerEmbedder classes in production.
"""

import json as json_module

import numpy as np

from worker.concepts import (
    GemmaConceptExtractor,
    OpenAIConceptExtractor,
    OpenAIEmbedder,
    RawConcept,
    cluster_concepts,
    extract_raw_concepts,
)
from worker.ingest import Chunk


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self._payload


def test_gemma_extractor_calls_local_endpoint_not_a_hosted_api(monkeypatch):
    captured = {}

    def fake_post(url, json=None, timeout=None):
        captured["url"] = url
        captured["timeout"] = timeout
        return _FakeResponse(
            {"response": json_module.dumps([{"name": "Derivatives", "definition": "Rate of change."}])}
        )

    monkeypatch.setattr("httpx.post", fake_post)

    extractor = GemmaConceptExtractor(base_url="http://localhost:11434", model="gemma2:9b")
    chunk = Chunk(doc_id="d.pdf", chunk_id="d.pdf:p1", page=1, text="Derivatives measure rate of change.")

    concepts = extractor.extract(chunk)

    assert captured["url"] == "http://localhost:11434/api/generate"
    assert concepts == [RawConcept(name="Derivatives", definition="Rate of change.", chunk_id="d.pdf:p1")]


def test_extract_raw_concepts_aggregates_across_chunks():
    class _FakeExtractor:
        def extract(self, chunk: Chunk) -> list[RawConcept]:
            return [RawConcept(name=chunk.text, definition="stub", chunk_id=chunk.chunk_id)]

    chunks = [
        Chunk(doc_id="d", chunk_id="d:p1", page=1, text="Concept A"),
        Chunk(doc_id="d", chunk_id="d:p2", page=2, text="Concept B"),
    ]

    raw = extract_raw_concepts(chunks, _FakeExtractor())

    assert [c.name for c in raw] == ["Concept A", "Concept B"]
    assert [c.chunk_id for c in raw] == ["d:p1", "d:p2"]


_VECTORS = {
    "gradient descent: An iterative optimization method.": [1.0, 0.0],
    "the steepest-descent optimization algorithm: Iteratively moves downhill.": [0.99, 0.05],
    "linear regression: Fits a line to data.": [0.0, 1.0],
}


def _fake_embed(texts: list[str]) -> np.ndarray:
    return np.array([_VECTORS[text] for text in texts])


def test_cluster_concepts_merges_near_duplicate_phrasings():
    raw = [
        RawConcept("gradient descent", "An iterative optimization method.", "c1"),
        RawConcept("the steepest-descent optimization algorithm", "Iteratively moves downhill.", "c2"),
        RawConcept("linear regression", "Fits a line to data.", "c3"),
    ]

    canonical = cluster_concepts(raw, _fake_embed, similarity_threshold=0.9)

    assert len(canonical) == 2
    merged = next(c for c in canonical if set(c.chunk_ids) == {"c1", "c2"})
    assert merged.name == "gradient descent"  # shorter of the two near-duplicate names wins
    solo = next(c for c in canonical if c.chunk_ids == ["c3"])
    assert solo.name == "linear regression"


def test_cluster_concepts_empty_input_returns_empty_list():
    assert cluster_concepts([], _fake_embed) == []


def test_openai_concept_extractor_posts_to_chat_completions_and_parses_concepts(monkeypatch):
    # Prototyping-only path (LLM_PROVIDER=openai) — see worker/main.py.
    # Confirms it hits OpenAI's chat-completions shape (not Ollama's
    # /api/generate), and unwraps the {"concepts": [...]} envelope the
    # prompt asks for (JSON mode requires a top-level object, not a bare
    # list, unlike GemmaConceptExtractor's Ollama-style "format": "json").
    captured = {}

    class _FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {
                "choices": [
                    {
                        "message": {
                            "content": json_module.dumps(
                                {"concepts": [{"name": "Derivatives", "definition": "Rate of change."}]}
                            )
                        }
                    }
                ]
            }

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return _FakeResponse()

    monkeypatch.setattr("httpx.post", fake_post)

    extractor = OpenAIConceptExtractor(api_key="test-key", model="gpt-4o-mini")
    chunk = Chunk(doc_id="d.pdf", chunk_id="d.pdf:p1", page=1, text="Derivatives measure rate of change.")

    concepts = extractor.extract(chunk)

    assert captured["url"] == "https://api.openai.com/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["json"]["response_format"] == {"type": "json_object"}
    assert concepts == [RawConcept(name="Derivatives", definition="Rate of change.", chunk_id="d.pdf:p1")]


def test_openai_embedder_posts_to_embeddings_endpoint_and_preserves_order(monkeypatch):
    captured = {}

    class _FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            # Deliberately returned out of order — the client must sort by
            # "index" before returning, since callers rely on output order
            # matching input order (e.g. cluster_concepts zips vectors back
            # to raw_concepts positionally).
            return {
                "data": [
                    {"index": 1, "embedding": [0.0, 1.0]},
                    {"index": 0, "embedding": [1.0, 0.0]},
                ]
            }

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        return _FakeResponse()

    monkeypatch.setattr("httpx.post", fake_post)

    embedder = OpenAIEmbedder(api_key="test-key", model="text-embedding-3-small")
    vectors = embedder(["first", "second"])

    assert captured["url"] == "https://api.openai.com/v1/embeddings"
    assert captured["json"] == {"model": "text-embedding-3-small", "input": ["first", "second"]}
    assert vectors.tolist() == [[1.0, 0.0], [0.0, 1.0]]
