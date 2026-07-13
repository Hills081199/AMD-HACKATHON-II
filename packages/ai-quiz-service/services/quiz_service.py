from llm.base import BaseLLMClient
from prompts.quiz_prompt import QuizPromptBuilder
from schemas.generation import QuizGenerationResult
from schemas.quiz import Quiz
from schemas.request import GenerateQuizRequest


class QuizService:
    """
    Handles the business logic
    for quiz generation.
    """

    def __init__(
        self,
        llm_client: BaseLLMClient,
    ):
        self.llm = llm_client

    def generate_quiz(
        self,
        request: GenerateQuizRequest,
    ) -> Quiz:

        prompt = QuizPromptBuilder.create_prompt(
            title=request.title,
            content=request.content,
            mcq_count=request.mcq_count,
            open_ended_count=request.open_ended_count,
        )

        generation = self.llm.generate(
            prompt=prompt,
            response_schema=QuizGenerationResult,
        )

        return Quiz(
            node_id=request.node_id,
            node_title=request.title,
            questions=generation.questions,
        )