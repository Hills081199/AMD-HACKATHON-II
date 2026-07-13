"""Tests for checkpoint-quiz grading (feat-008)."""

from app.services.quiz import grade_quiz

_QUIZ = {
    "pass_threshold": 0.7,
    "questions": [
        {"id": "q1", "answer_index": 1},
        {"id": "q2", "answer_index": 0},
        {"id": "q3", "answer_index": 2},
    ],
}


def test_grade_quiz_all_correct_passes():
    result = grade_quiz(_QUIZ, {"q1": 1, "q2": 0, "q3": 2})

    assert result == {"score": 1.0, "correct": 3, "total": 3, "passed": True}


def test_grade_quiz_below_threshold_fails():
    result = grade_quiz(_QUIZ, {"q1": 1, "q2": 9, "q3": 9})

    assert result["score"] < 0.7
    assert result["passed"] is False
    assert result["correct"] == 1


def test_grade_quiz_missing_answers_count_as_wrong():
    result = grade_quiz(_QUIZ, {"q1": 1})

    assert result == {"score": 1 / 3, "correct": 1, "total": 3, "passed": False}


def test_grade_quiz_single_question_meets_threshold_exactly():
    quiz = {"pass_threshold": 0.7, "questions": [{"id": "q1", "answer_index": 1}]}

    result = grade_quiz(quiz, {"q1": 1})

    assert result == {"score": 1.0, "correct": 1, "total": 1, "passed": True}
