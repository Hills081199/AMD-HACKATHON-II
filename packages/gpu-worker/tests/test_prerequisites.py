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
    """With max_all_pairs smaller than the dataset size, similarity filtering kicks in."""
    all_pairs = list(combinations(range(len(_CONCEPTS)), 2))
    # Pass max_all_pairs=5 so the all-pairs shortcut doesn't trigger (dataset has 6 concepts)
    filtered = pre_filter_pairs(_CONCEPTS, similarity_threshold=0.9, max_all_pairs=5)

    assert len(all_pairs) == 15  # C(6, 2) — what an unfiltered scan would cost
    assert (0, 1) in filtered and (2, 3) in filtered and (4, 5) in filtered
    assert len(filtered) < len(all_pairs)


def test_pre_filter_pairs_fewer_than_two_concepts_returns_empty():
    assert pre_filter_pairs(_CONCEPTS[:1], similarity_threshold=0.9, max_all_pairs=5) == []
    assert pre_filter_pairs([], similarity_threshold=0.9, max_all_pairs=5) == []


def test_pre_filter_pairs_all_pairs_when_small_dataset():
    """IMP-A2 — when len(concepts) <= max_all_pairs, ALL pairs are returned
    (no similarity filtering) to avoid missing prerequisite relationships."""
    # 6 concepts, max_all_pairs=10 → all-pairs shortcut fires
    all_pairs_expected = list(combinations(range(len(_CONCEPTS)), 2))
    filtered = pre_filter_pairs(_CONCEPTS, similarity_threshold=0.9, max_all_pairs=10)
    assert sorted(filtered) == sorted(all_pairs_expected)


class _FakeFireworks:
    """Records every pair it's asked about and returns a canned direction."""

    def __init__(self, directions: dict[tuple[str, str], dict]):
        self.directions = directions
        self.calls: list[tuple[str, str]] = []

    def infer_direction(self, concept_a: dict, concept_b: dict, **kwargs) -> dict:
        """Accept but ignore all_concepts/domain kwargs — only the core pair
        matters for unit-testing the call routing logic."""
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

    # Wrap build_candidate_edges so pre_filter_pairs uses max_all_pairs=5,
    # forcing similarity-based filtering (6 concepts > 5) instead of all-pairs.
    from worker import prerequisites as prereqs_mod
    import unittest.mock as mock
    original_pfp = prereqs_mod.pre_filter_pairs
    def patched_pfp(concepts, similarity_threshold=0.35, max_all_pairs=None):
        return original_pfp(concepts, similarity_threshold=similarity_threshold, max_all_pairs=5)
    with mock.patch.object(prereqs_mod, "pre_filter_pairs", side_effect=patched_pfp):
        edges = build_candidate_edges(_CONCEPTS, fake, similarity_threshold=0.9, min_confidence=0.5)

    # 3 pre-filtered pairs, not all 15 — proving the O(n^2) scan was avoided.
    assert set(fake.calls) == {("concept_001", "concept_002"), ("concept_003", "concept_004"), ("concept_005", "concept_006")}
    # Both 0.91 and 0.77 pass the default min_confidence=0.5 threshold.
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


def test_fireworks_client_defaults_to_fireworks_when_llm_provider_unset(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.setenv("FIREWORKS_API_KEY", "fw-key")

    client = FireworksClient()

    assert client.base_url == "https://api.fireworks.ai/inference/v1"
    assert client.model == "accounts/fireworks/models/llama-v3p1-8b-instruct"
    assert client.api_key == "fw-key"


def test_fireworks_client_switches_to_openai_when_llm_provider_is_openai(monkeypatch):
    # Prototyping-only switch (docs/hackathon-scope.md §5) to validate this
    # step against GPT-4o mini before a real Fireworks account exists —
    # safe because Fireworks' API is itself OpenAI-compatible, so only the
    # credentials/base_url/model need to change, not the request shape.
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    client = FireworksClient()

    assert client.base_url == "https://api.openai.com/v1"
    assert client.model == "gpt-4o-mini"
    assert client.api_key == "sk-test"


def test_fireworks_client_explicit_args_override_llm_provider_switch(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")

    client = FireworksClient(api_key="explicit-key", base_url="https://example.com/v1", model="explicit-model")

    assert client.api_key == "explicit-key"
    assert client.base_url == "https://example.com/v1"
    assert client.model == "explicit-model"


# ── IMP-4.1: confidence threshold filtering ─────────────────────────────────

def test_low_confidence_edge_dropped():
    """IMP-4.1 — edges below min_confidence must be silently discarded so that
    spurious LLM guesses do not pollute the prerequisite graph."""
    fake = _FakeFireworks(
        {
            # High confidence: keeps
            ("concept_001", "concept_002"): {"direction": "a_before_b", "confidence": 0.91},
            # Low confidence (< 0.6 default): must be dropped
            ("concept_003", "concept_004"): {"direction": "a_before_b", "confidence": 0.4},
            # Boundary exactly at min_confidence (0.6): keeps
            ("concept_005", "concept_006"): {"direction": "b_before_a", "confidence": 0.6},
        }
    )

    edges = build_candidate_edges(_CONCEPTS, fake, similarity_threshold=0.9, min_confidence=0.6)

    edge_pairs = {(e["from"], e["to"]) for e in edges}
    assert ("concept_001", "concept_002") in edge_pairs, "High-confidence edge should be kept"
    assert ("concept_006", "concept_005") in edge_pairs, "Edge exactly at min_confidence should be kept"
    # concept_003/004 produced confidence=0.4 which is < 0.6 — must NOT appear
    assert not any(
        {e["from"], e["to"]} == {"concept_003", "concept_004"} for e in edges
    ), "Low-confidence edge (0.4) should have been dropped"

    # Reset _MAX_ALL_PAIRS side-effect if needed (test uses explicit min_confidence arg so pre_filter
    # behaviour doesn't affect this assertion)


# ── IMP-4.2: JSON error handling ────────────────────────────────────────────

def test_infer_direction_handles_malformed_json(monkeypatch):
    """IMP-4.2 — if the LLM returns malformed JSON for all 3 retry attempts the
    call must not raise; instead it returns {'direction': 'none', 'confidence': 0.0}
    so that build_candidate_edges can continue processing other pairs."""
    call_count = 0

    class _BadResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {
                "choices": [{"message": {"content": "not valid json {{{"}  }]
            }

    def always_bad_post(url, headers=None, json=None, timeout=None):
        nonlocal call_count
        call_count += 1
        return _BadResponse()

    monkeypatch.setattr("httpx.post", always_bad_post)

    client = FireworksClient(api_key="test-key", base_url="https://api.fireworks.ai/inference/v1", model="test-model")
    result = client.infer_direction(
        {"name": "A", "definition": "desc A"},
        {"name": "B", "definition": "desc B"},
    )

    assert result == {"direction": "none", "confidence": 0.0}, (
        "Malformed JSON should degrade to 'none' rather than raising"
    )
    assert call_count == 3, "Should have retried exactly 3 times before giving up"


# ── IMP-4.5: definition-containment pre-filter ────────────────────────────

def test_definition_containment_pair_included():
    """IMP-4.5 — when concept A's name appears in concept B's definition,
    the pair must be included even if their embedding similarity is below
    the similarity_threshold.  This captures cross-domain prerequisite links
    that pure cosine similarity would miss."""
    # 'Matrix' appears in 'Matrix Multiplication''s definition — strong signal
    # that Matrix is a prerequisite.  Embeddings are intentionally far apart
    # (orthogonal) so they would NOT pass the similarity threshold alone.
    concepts = [
        {
            "id": "c1",
            "name": "Matrix",
            "definition": "A rectangular array of numbers arranged in rows and columns.",
            "embedding": [1.0, 0.0, 0.0],
        },
        {
            "id": "c2",
            "name": "Matrix Multiplication",
            "definition": "An operation that multiplies two matrix objects to produce a new matrix.",
            "embedding": [0.0, 1.0, 0.0],   # orthogonal — cosine sim = 0.0 < threshold
        },
        {
            "id": "c3",
            "name": "Probability",
            "definition": "The measure of the likelihood that an event will occur.",
            "embedding": [0.0, 0.0, 1.0],   # unrelated to both
        },
    ]

    # Use a high similarity threshold AND override max_all_pairs=2 (< 3 concepts)
    # to ensure the similarity-based filter path is exercised, not all-pairs.
    # With 3 concepts and max_all_pairs=2, similarity filter applies:
    #   - (0,1): orthogonal embeddings, similarity=0 < 0.95 -> Strategy 1 fails
    #   - But Strategy 3 (definition containment): 'matrix' in 'matrix objects' -> included
    pairs = pre_filter_pairs(concepts, similarity_threshold=0.95, max_all_pairs=2)

    pair_set = set(pairs)
    assert (0, 1) in pair_set, (
        "(Matrix, Matrix Multiplication) must be included via definition containment "
        "even though their embeddings are orthogonal"
    )
    # (0, 2) and (1, 2) should NOT be included — no definition containment or similarity
    assert (0, 2) not in pair_set, "Unrelated pair should not be pulled in"
    assert (1, 2) not in pair_set, "Unrelated pair should not be pulled in"


def test_pre_filter_pairs_difficulty_pairs_always_included():
    """IMP-A3 bonus: foundational ↔ advanced pairs are always included
    regardless of embedding similarity when the dataset is large enough
    to trigger similarity-based filtering (max_all_pairs < len(concepts))."""
    import worker.prerequisites as prereqs_mod
    orig = prereqs_mod._MAX_ALL_PAIRS
    prereqs_mod._MAX_ALL_PAIRS = 2  # force similarity-based filter path
    try:
        concepts = [
            {"id": "c1", "name": "Variable", "definition": "A storage location.",
             "difficulty": "foundational", "embedding": [1.0, 0.0, 0.0]},
            {"id": "c2", "name": "Pointer Arithmetic", "definition": "Advanced memory manipulation.",
             "difficulty": "advanced", "embedding": [0.0, 1.0, 0.0]},  # orthogonal to c1
            {"id": "c3", "name": "Loop", "definition": "A control structure.",
             "difficulty": "intermediate", "embedding": [0.0, 0.0, 1.0]},
        ]
        pairs = pre_filter_pairs(concepts, similarity_threshold=0.95)
    finally:
        prereqs_mod._MAX_ALL_PAIRS = orig

    pair_set = set(pairs)
    # foundational ↔ advanced pair must be included despite orthogonal embeddings
    assert (0, 1) in pair_set, "Foundational↔Advanced pair should always be included"
