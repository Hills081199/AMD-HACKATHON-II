from pydantic import BaseModel, Field


class GenerateQuizRequest(BaseModel):
    node_id: str

    title: str

    content: str = Field(min_length=50)

    mcq_count: int = Field(default=5, ge=0, le=20)

    open_ended_count: int = Field(default=2, ge=0, le=10)