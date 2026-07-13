"""End-to-end test of POST /trees/{topic_id}/nodes/{node_id}/lesson, with a
fake Fireworks client swapped in via FastAPI dependency overrides so no real
Fireworks API key or network access is required."""

from fastapi.testclient import TestClient

from app.main import app
from app.routers.teach import get_fireworks_client


class _FakeFireworks:
    def generate(self, node_name, chunks):
        return {
            "lesson": f"Lesson about {node_name}, grounded in {len(chunks)} source chunk(s).",
            "quiz": {"question": "Why?", "options": ["a", "b"], "answer_index": 0},
            "example": "Some real-world example.",
        }

    def check_alignment(self, node_name, lesson, quiz):
        return True


def test_lesson_endpoint_returns_lesson_quiz_example_scoped_to_given_sources():
    app.dependency_overrides[get_fireworks_client] = lambda: _FakeFireworks()
    try:
        client = TestClient(app)
        payload = {
            "node_name": "Gradient Descent",
            "chunks": [
                {"chunk_id": "doc_001:p6", "doc_id": "doc_001", "page": 6, "text": "Gradient descent details."}
            ],
        }
        response = client.post("/trees/intro-to-ml/nodes/n4/lesson", json=payload)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["lesson"] == "Lesson about Gradient Descent, grounded in 1 source chunk(s)."
    assert body["sources"] == [{"chunk_id": "doc_001:p6", "doc_id": "doc_001", "page": 6}]
    assert body["self_check"] == {"passed": True, "attempts": 1}
