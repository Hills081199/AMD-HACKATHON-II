"""Checkpoint quiz grading — see docs/concept-graph-pipeline.md's unlock
mechanism: a node becomes `completed` once its checkpoint quiz is passed,
which is what lets feat-006's unlock logic flip its children from locked to
unlocked."""

from __future__ import annotations


def grade_quiz(quiz: dict, answers: dict[str, int]) -> dict:
    """Grade a submitted answer set against a node's quiz definition
    (questions[] with id/answer_index, pass_threshold). Returns
    {"score": float, "correct": int, "total": int, "passed": bool,
     "correctAnswers": dict mapping question_id -> correct option index}."""
    questions = quiz.get("questions", [])
    total = len(questions)
    correct = sum(1 for question in questions if answers.get(question["id"]) == question["answer_index"])
    score = correct / total if total else 0.0
    passed = score >= quiz.get("pass_threshold", 1.0)
    # Build mapping of question_id -> correct answer index for frontend display
    correct_answers = {q["id"]: q["answer_index"] for q in questions}
    return {"score": score, "correct": correct, "total": total, "passed": passed, "correctAnswers": correct_answers}
