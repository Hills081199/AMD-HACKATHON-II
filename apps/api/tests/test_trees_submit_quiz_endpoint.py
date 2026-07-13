"""End-to-end test of POST /trees/{topic_id}/nodes/{node_id}/submit-quiz
(feat-008), against the real checked-in sample dataset (n3 "Loss Functions"
has one MCQ question q_n3_1 with answer_index 1 and pass_threshold 0.7)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_submit_quiz_with_correct_answers_passes():
    response = client.post(
        "/trees/intro-to-ml/nodes/n3/submit-quiz",
        json={"answers": {"q_n3_1": 1}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["node_id"] == "n3"
    assert body["passed"] is True
    assert body["score"] == 1.0
    # Verify correctAnswers is returned for frontend display
    assert "correctAnswers" in body
    assert body["correctAnswers"]["q_n3_1"] == 1


def test_submit_quiz_with_wrong_answers_fails():
    response = client.post(
        "/trees/intro-to-ml/nodes/n3/submit-quiz",
        json={"answers": {"q_n3_1": 0}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["passed"] is False
    assert body["score"] == 0.0
    # Even on failure, correctAnswers should be returned so user can see the right answers
    assert "correctAnswers" in body
    assert body["correctAnswers"]["q_n3_1"] == 1


def test_submit_quiz_for_unknown_node_returns_404():
    response = client.post(
        "/trees/intro-to-ml/nodes/does-not-exist/submit-quiz",
        json={"answers": {}},
    )

    assert response.status_code == 404
