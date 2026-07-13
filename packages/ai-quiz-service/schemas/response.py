from pydantic import BaseModel

from schemas.quiz import Quiz


class GenerateQuizResponse(BaseModel):
    success: bool

    message: str

    quiz: Quiz