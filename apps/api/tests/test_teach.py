"""Tests for pipeline step 7, per-node lesson + quiz + real-world example
(agentic RAG) — see docs/concept-graph-pipeline.md's Teach stage."""

from app.services.teach import FireworksClient, generate_lesson_package


class FakeFireworks:
    """Records every call so tests can assert exactly which chunks were
    sent (retrieval scoping) and how many generate/check_alignment round
    trips happened (self-check retry behavior)."""

    def __init__(self, alignment_sequence):
        self.alignment_sequence = list(alignment_sequence)
        self.generate_calls: list[tuple[str, list[dict]]] = []
        self.check_calls: list[tuple[str, dict]] = []

    def generate(self, node_name, chunks):
        self.generate_calls.append((node_name, chunks))
        attempt = len(self.generate_calls)
        return {
            "lesson": f"Lesson v{attempt} about {node_name}.",
            "quiz": {"question": f"Q v{attempt}?", "options": ["a", "b"], "answer_index": 0},
            "example": f"Example v{attempt}.",
        }

    def check_alignment(self, node_name, lesson, quiz):
        self.check_calls.append((lesson, quiz))
        return self.alignment_sequence[len(self.check_calls) - 1]


def _chunks():
    return [
        {"chunk_id": "doc_001:p3", "doc_id": "doc_001", "page": 3, "text": "Gradient descent minimizes loss."},
        {"chunk_id": "doc_001:p4", "doc_id": "doc_001", "page": 4, "text": "Learning rate controls step size."},
    ]


def test_generate_lesson_package_passes_self_check_on_first_attempt():
    fireworks = FakeFireworks(alignment_sequence=[True])

    result = generate_lesson_package("Gradient Descent", _chunks(), fireworks)

    assert len(fireworks.generate_calls) == 1
    assert result["lesson"] == "Lesson v1 about Gradient Descent."
    assert result["self_check"] == {"passed": True, "attempts": 1}
    assert result["sources"] == [
        {"chunk_id": "doc_001:p3", "doc_id": "doc_001", "page": 3},
        {"chunk_id": "doc_001:p4", "doc_id": "doc_001", "page": 4},
    ]


def test_generate_lesson_package_retrieval_is_scoped_to_only_this_nodes_chunks():
    fireworks = FakeFireworks(alignment_sequence=[True])
    chunks = _chunks()

    generate_lesson_package("Gradient Descent", chunks, fireworks)

    # Exactly the two chunks passed in were sent — nothing from a wider
    # corpus was added, proving this isn't whole-corpus prompting.
    sent_node_name, sent_chunks = fireworks.generate_calls[0]
    assert sent_node_name == "Gradient Descent"
    assert sent_chunks == chunks


def test_generate_lesson_package_regenerates_on_a_forced_quiz_lesson_mismatch():
    # First attempt's quiz is deliberately misaligned with its lesson;
    # forces the self-check guard to fire and trigger a real regeneration.
    fireworks = FakeFireworks(alignment_sequence=[False, True])

    result = generate_lesson_package("Gradient Descent", _chunks(), fireworks, max_attempts=2)

    assert len(fireworks.generate_calls) == 2
    assert len(fireworks.check_calls) == 2
    assert result["lesson"] == "Lesson v2 about Gradient Descent."
    assert result["self_check"] == {"passed": True, "attempts": 2}


def test_generate_lesson_package_flags_unpassed_self_check_after_exhausting_attempts():
    # Every attempt fails alignment; the function must still return a
    # result (the last attempt) rather than raising, but flag it clearly.
    fireworks = FakeFireworks(alignment_sequence=[False, False])

    result = generate_lesson_package("Gradient Descent", _chunks(), fireworks, max_attempts=2)

    assert len(fireworks.generate_calls) == 2
    assert result["self_check"] == {"passed": False, "attempts": 2}
    assert result["lesson"] == "Lesson v2 about Gradient Descent."


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
