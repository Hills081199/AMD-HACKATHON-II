from llm.base import BaseLLMClient
from prompts.review_prompt import ReviewPromptBuilder
from schemas.quiz import Quiz
from schemas.review import QuizReviewResult


class QuizReviewer:
    def __init__(self, llm_client: BaseLLMClient):
        self.llm = llm_client

    def review_quiz(self, quiz: Quiz) -> QuizReviewResult:
        prompt = ReviewPromptBuilder.create_prompt(
            title=quiz.node_title,
            content="\n".join(question.question for question in quiz.questions),
        )
        return self.llm.generate(prompt=prompt, response_schema=QuizReviewResult)
