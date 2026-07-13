from typing import List, Literal, Optional

from pydantic import BaseModel

from schemas.enums import (
    BloomLevel,
    Difficulty,
    QuestionType,
)


class Option(BaseModel):
    id: Literal["A", "B", "C", "D"]
    text: str


class RubricItem(BaseModel):
    criterion: str
    marks: int


class Question(BaseModel):
    id: str

    type: QuestionType

    learning_objective: str

    question: str

    options: Optional[List[Option]] = None

    correct_answer: Literal["A", "B", "C", "D"]

    explanation: str

    difficulty: Difficulty

    bloom_level: BloomLevel

    estimated_time_seconds: int

    tags: List[str]

    rubric: Optional[List[RubricItem]] = None