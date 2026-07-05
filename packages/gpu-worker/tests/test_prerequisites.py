"""Tests for pipeline step 4 (docs/concept-graph-pipeline.md).

Uses a fake Fireworks client and synthetic embeddings so the suite never
needs a live Fireworks API key or network access — only worker/main.py's
dependency-injected /build-graph endpoint touches the real FireworksClient
in production.
"""

from itertools import combinations

from worker.prerequisites import FireworksClient, build_candidate_edges, pre_filter_pairs


def _concept(concept_id: str, name: str, definition: str, embedding: list[float]) -> dict:
    return {"id": concept_id, "name": name, "definition": definition, "embedding": embedding}


# Three tight clusters of near-identical vectors (within a cluster) and far
# apart across clusters, so only within-cluster pairs should survive
# pre-filtering — a stand-in for "most concept pairs aren't plausible
# prerequisites of each other."
_CONCEPTS = [
    _concept("concept_001", "Vectors", "...", [1.0, 0.0, 0.0]),
    _concept("concept_002", "Matrices", "...", [0.98, 0.05, 0.0]),
    _concept("concept_003", "Gradient descent", "...", [0.0, 1.0, 0.0]),
    _concept("concept_004", "Backpropagation", "...", [0.0, 0.97, 0.06]),
    _concept("concept_005", "Probability", "...", [0.0, 0.0, 1.0]),
    _concept("concept_006", "Bayes' theorem", "...", [0.0, 0.05, 0.98]),
]


def test_pre_filter_pairs_avoids_full_all_pairs_scan():
    all_pairs = list(combinations(range(len(_CONCEPTS)), 2))
    filtered = pre_filter_pairs(_CONCEPTS, similarity_threshold=0.9)

    assert len(all_pairs) == 15  # C(6, 2) — what an unfiltered scan would cost
    assert filtered == [(0, 1), (2, 3), (4, 5)]
    assert len(filtered) < len(all_pairs)


def test_pre_filter_pairs_fewer_than_two_concepts_returns_empty():
    assert pre_filter_pairs(_CONCEPTS[:1], similarity_threshold=0.9) == []
    assert pre_filter_pairs([], similarity_threshold=0.9) == []


class _FakeFireworks:
    """Records every pair it's asked about and returns a canned direction."""

    def __init__(self, directions: dict[tuple[str, str], dict]):
        self.directions = directions
        self.calls: list[tuple[str, str]] = []

    def infer_direction(self, concept_a: dict, concept_b: dict) -> dict:
        self.calls.append((concept_a["id"], concept_b["id"]))
        return self.directions.get((concept_a["id"], concept_b["id"]), {"direction": "none", "confidence": 0.0})


def test_build_candidate_edges_only_calls_fireworks_for_prefiltered_pairs():
    fake = _FakeFireworks(
        {
            ("concept_001", "concept_002"): {"direction": "a_before_b", "confidence": 0.91},
            ("concept_003", "concept_004"): {"direction": "b_before_a", "confidence": 0.77},
            ("concept_005", "concept_006"): {"direction": "none", "confidence": 0.2},
        }
    )

    edges = build_candidate_edges(_CONCEPTS, fake, similarity_threshold=0.9)

    # 3 pre-filtered pairs, not all 15 — proving the O(n^2) scan was avoided.
    assert fake.calls == [("concept_001", "concept_002"), ("concept_003", "concept_004"), ("concept_005", "concept_006")]
    assert {"from": "concept_001", "to": "concept_002", "confidence": 0.91} in edges
    assert {"from": "concept_004", "to": "concept_003", "confidence": 0.77} in edges
    assert len(edges) == 2  # the "none" pair produces no edge


def test_fireworks_client_posts_to_configured_chat_completions_endpoint(monkeypatch):
    captured = {}

    class _FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {
                "choices": [
                    {"message": {"content": '{"direction": "a_before_b", "confidence": 0.8}'}}
                ]
            }

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return _FakeResponse()

    monkeypatch.setattr("httpx.post", fake_post)

    client = FireworksClient(api_key="test-key", base_url="https://api.fireworks.ai/inference/v1", model="test-model")
    result = client.infer_direction(
        {"name": "Derivatives", "definition": "Rate of change."},
        {"name": "Gradient descent", "definition": "Iterative optimization."},
    )

    assert captured["url"] == "https://api.fireworks.ai/inference/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["json"]["model"] == "test-model"
    assert result == {"direction": "a_before_b", "confidence": 0.8}
