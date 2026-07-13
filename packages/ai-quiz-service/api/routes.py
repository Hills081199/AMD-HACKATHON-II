import traceback

from fastapi import APIRouter, HTTPException

from llm.exceptions import GeminiGenerationError
from llm.gemini_client import GeminiClient
from schemas.request import GenerateQuizRequest
from schemas.response import GenerateQuizResponse
from services.quiz_service import QuizService

router = APIRouter(
    prefix="/api/v1/quizzes",
    tags=["Quiz Generation"],
)

# Create service instances
llm_client = GeminiClient()
quiz_service = QuizService(llm_client)


@router.post(
    "/generate",
    response_model=GenerateQuizResponse,
    summary="Generate quiz from a mastery node",
)
def generate_quiz(request: GenerateQuizRequest):
    """
    Generate MCQ and open-ended questions
    from a single Mastery Tree node.
    """

    try:
        quiz = quiz_service.generate_quiz(request)

        return GenerateQuizResponse(
            success=True,
            message="Quiz generated successfully.",
            quiz=quiz,
        )

    except GeminiGenerationError as e:
        # Expected AI generation errors
        traceback.print_exc()

        raise HTTPException(
            status_code=503,
            detail=f"Gemini Generation Error: {str(e)}",
        )

    except Exception as e:
        # Unexpected errors
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error: {str(e)}",
        )