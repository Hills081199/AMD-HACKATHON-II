from llm.gemini_client import GeminiClient
from services.quiz_service import QuizService


def get_quiz_service():

    llm = GeminiClient()

    return QuizService(llm)