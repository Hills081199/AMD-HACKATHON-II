from typing import List

from pydantic import BaseModel

from schemas.question import Question


class QuizGenerationResult(BaseModel):
    questions: List[Question]