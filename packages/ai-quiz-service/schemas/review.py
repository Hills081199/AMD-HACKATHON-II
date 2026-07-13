from typing import List

from pydantic import BaseModel

from schemas.review_enums import (
    ReviewCategory,
    ReviewSeverity,
)


class ReviewIssue(BaseModel):
    """
    Represents one issue found during quiz review.
    """

    question_id: str

    category: ReviewCategory

    severity: ReviewSeverity

    message: str


class ReviewReport(BaseModel):
    """
    Overall review result returned by the AI reviewer.
    """

    approved: bool

    overall_score: int

    issues: List[ReviewIssue]