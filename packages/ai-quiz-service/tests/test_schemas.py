from fastapi.testclient import TestClient

from main import app
from schemas import QuizCreateRequest, QuizResponse


client = TestClient(app)


def test_quiz_request_schema_accepts_valid_input():
    payload = QuizCreateRequest(topic="Python", difficulty="medium", number_of_questions=3)
    assert payload.topic == "Python"
    assert payload.number_of_questions == 3


def test_quiz_response_schema_allows_questions_list():
    response = QuizResponse(id="1", topic="Python", difficulty="easy", questions=[])
    assert response.questions == []


def test_quiz_creation_endpoint_returns_quiz_payload():
    response = client.post(
        "/api/v1/quizzes",
        json={"topic": "Python", "difficulty": "medium", "number_of_questions": 2},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["topic"] == "Python"
    assert payload["difficulty"] == "medium"
    assert len(payload["questions"]) >= 1
