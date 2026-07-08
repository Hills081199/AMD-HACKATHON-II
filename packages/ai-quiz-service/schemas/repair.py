from typing import List

from pydantic import BaseModel, Field


class RepairAction(BaseModel):
    target: str
    change: str


class QuizRepairResult(BaseModel):
    summary: str
    actions: List[RepairAction] = Field(default_factory=list)
