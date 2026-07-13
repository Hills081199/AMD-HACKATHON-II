from datetime import datetime
from typing import List
from uuid import uuid4

from pydantic import BaseModel, Field

from schemas.question import Question


class Quiz(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))

    node_id: str

    node_title: str

    generated_at: datetime = Field(default_factory=datetime.utcnow)

    questions: List[Question]