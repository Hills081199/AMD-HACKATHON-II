from llm.base import BaseLLMClient
from prompts.repair_prompt import RepairPromptBuilder
from prompts.review_prompt import ReviewPromptBuilder
from reviewers.quiz_reviewer import QuizReviewer
from schemas.quiz import Quiz
from schemas.repair import QuizRepairResult, RepairAction
from schemas.review import QuizReviewResult, ReviewFinding
from services.review_service import ReviewService


class FakeLLMClient(BaseLLMClient):
    def generate(self, prompt: str, response_schema):
        if response_schema is QuizReviewResult:
            return QuizReviewResult(
                overall_score=0.9,
                summary="The quiz is well structured.",
                findings=[ReviewFinding(category="accuracy", message="No issues detected.")],
            )
        if response_schema is QuizRepairResult:
            return QuizRepairResult(
                summary="A minor repair was applied.",
                actions=[RepairAction(target="question_1", change="Adjusted the explanation.")],
            )
        raise AssertionError("Unexpected response schema")


def test_review_and_repair_schemas_accept_expected_fields():
    finding = ReviewFinding(category="accuracy", message="Needs factual grounding")
    review = QuizReviewResult(overall_score=0.8, summary="Looks good", findings=[finding])
    repair = QuizRepairResult(summary="Repaired", actions=[RepairAction(target="question_1", change="Updated the option text")])

    assert review.findings[0].category == "accuracy"
    assert repair.actions[0].target == "question_1"


def test_prompt_builders_return_non_empty_strings():
    review_prompt = ReviewPromptBuilder.create_prompt("Python Basics", "Variables and loops")
    repair_prompt = RepairPromptBuilder.create_prompt("Python Basics", "Variables and loops", "[]")

    assert "review" in review_prompt.lower()
    assert "repair" in repair_prompt.lower()
    assert len(review_prompt) > 0
    assert len(repair_prompt) > 0


def test_review_service_and_reviewer_work_with_stubbed_llm():
    quiz = Quiz(node_id="node-1", node_title="Python Basics", questions=[])
    llm_client = FakeLLMClient()

    review_service = ReviewService(llm_client=llm_client)
    reviewer = QuizReviewer(llm_client=llm_client)

    review_result = review_service.review_quiz(quiz)
    repair_result = review_service.repair_quiz(quiz, review_result)
    reviewer_result = reviewer.review_quiz(quiz)

    assert review_result.overall_score == 0.9
    assert repair_result.actions[0].target == "question_1"
    assert reviewer_result.overall_score == 0.9
