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


def test_extract_raw_concepts_batches_to_reduce_call_count():
    # The whole point of the optimization: with batch_size=5, 12 chunks must
    # trigger only ceil(12/5)=3 batched LLM calls, not 12 per-chunk calls,
    # and every concept must still map back to its own chunk_id.
    class _CountingBatchExtractor:
        def __init__(self):
            self.batch_calls = 0

        def extract_batch(self, chunks: list[Chunk]) -> list[RawConcept]:
            self.batch_calls += 1
            return [
                RawConcept(name=f"c-{chunk.chunk_id}", definition="stub", chunk_id=chunk.chunk_id)
                for chunk in chunks
            ]

    chunks = [Chunk(doc_id="d", chunk_id=f"d:p{i}", page=i, text=f"text {i}") for i in range(12)]
    extractor = _CountingBatchExtractor()

    raw = extract_raw_concepts(chunks, extractor, batch_size=5, max_workers=1)

    assert extractor.batch_calls == 3
    assert [c.chunk_id for c in raw] == [f"d:p{i}" for i in range(12)]


def test_extract_raw_concepts_falls_back_to_per_chunk_when_no_batch_method():
    class _CountingExtractor:
        def __init__(self):
            self.calls = 0

        def extract(self, chunk: Chunk) -> list[RawConcept]:
            self.calls += 1
            return [RawConcept(name=chunk.text, definition="stub", chunk_id=chunk.chunk_id)]

    chunks = [Chunk(doc_id="d", chunk_id=f"d:p{i}", page=i, text=f"C{i}") for i in range(3)]
    extractor = _CountingExtractor()

    raw = extract_raw_concepts(chunks, extractor, batch_size=5, max_workers=1)

    assert extractor.calls == 3  # no extract_batch -> one extract() per chunk
    assert [c.name for c in raw] == ["C0", "C1", "C2"]


def test_extract_raw_concepts_preserves_order_when_run_in_parallel():
    # With max_workers>1 the batches run concurrently; results must still come
    # back in input order (executor.map guarantees this), so downstream
    # clustering keeps a stable, deterministic concept list.
    class _BatchExtractor:
        def extract_batch(self, chunks: list[Chunk]) -> list[RawConcept]:
            return [
                RawConcept(name=chunk.text, definition="stub", chunk_id=chunk.chunk_id)
                for chunk in chunks
            ]

    chunks = [Chunk(doc_id="d", chunk_id=f"d:p{i}", page=i, text=f"C{i}") for i in range(10)]

    raw = extract_raw_concepts(chunks, _BatchExtractor(), batch_size=2, max_workers=4)

    assert [c.name for c in raw] == [f"C{i}" for i in range(10)]


def test_gemma_extract_batch_sends_one_call_and_maps_by_chunk_index(monkeypatch):
    captured = {}

    def fake_post(url, json=None, timeout=None):
        captured["url"] = url
        captured["calls"] = captured.get("calls", 0) + 1
        return _FakeResponse(
            {
                "response": json_module.dumps(
                    {
                        "results": [
                            {"chunk_index": 0, "concepts": [{"name": "Vectors", "definition": "d1"}]},
                            {"chunk_index": 1, "concepts": [{"name": "Gradients", "definition": "d2"}]},
                        ]
                    }
                )
            }
        )

    monkeypatch.setattr("httpx.post", fake_post)

    extractor = GemmaConceptExtractor(base_url="http://localhost:11434", model="gemma2:9b")
    chunks = [
        Chunk(doc_id="d.pdf", chunk_id="d.pdf:p1", page=1, text="About vectors."),
        Chunk(doc_id="d.pdf", chunk_id="d.pdf:p2", page=2, text="About gradients."),
    ]

    raw = extractor.extract_batch(chunks)

    assert captured["url"] == "http://localhost:11434/api/generate"
    assert captured["calls"] == 1  # two chunks, one HTTP call
    assert raw == [
        RawConcept(name="Vectors", definition="d1", chunk_id="d.pdf:p1"),
        RawConcept(name="Gradients", definition="d2", chunk_id="d.pdf:p2"),
    ]


def test_openai_extract_batch_sends_one_call_and_maps_by_chunk_index(monkeypatch):
    captured = {}

    class _FakeChatResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {
                "choices": [
                    {
                        "message": {
                            "content": json_module.dumps(
                                {
                                    "results": [
                                        {"chunk_index": 0, "concepts": [{"name": "Vectors", "definition": "d1"}]},
                                        {"chunk_index": 1, "concepts": [{"name": "Gradients", "definition": "d2"}]},
                                    ]
                                }
                            )
                        }
                    }
                ]
            }

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["calls"] = captured.get("calls", 0) + 1
        return _FakeChatResponse()

    monkeypatch.setattr("httpx.post", fake_post)

    extractor = OpenAIConceptExtractor(api_key="test-key", model="gpt-4o-mini")
    chunks = [
        Chunk(doc_id="d.pdf", chunk_id="d.pdf:p1", page=1, text="About vectors."),
        Chunk(doc_id="d.pdf", chunk_id="d.pdf:p2", page=2, text="About gradients."),
    ]

    raw = extractor.extract_batch(chunks)

    assert captured["url"] == "https://api.openai.com/v1/chat/completions"
    assert captured["calls"] == 1
    assert raw == [
        RawConcept(name="Vectors", definition="d1", chunk_id="d.pdf:p1"),
        RawConcept(name="Gradients", definition="d2", chunk_id="d.pdf:p2"),
    ]


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
