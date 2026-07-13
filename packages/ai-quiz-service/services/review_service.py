from llm.base import BaseLLMClient
from prompts.review_prompt import ReviewPromptBuilder
from schemas.quiz import Quiz
from schemas.review import ReviewReport


class ReviewService:
    """
    Reviews AI-generated quizzes for quality,
    correctness, and educational value.
    """

    def __init__(
        self,
        llm_client: BaseLLMClient,
    ):
        self.llm = llm_client

    def review_quiz(
        self,
        quiz: Quiz,
        title: str,
        content: str,
    ) -> ReviewReport:

        prompt = ReviewPromptBuilder.create_prompt(
            title=title,
            content=content,
            quiz=quiz.model_dump(),
        )

        review = self.llm.generate(
            prompt=prompt,
            response_schema=ReviewReport,
        )

        return review