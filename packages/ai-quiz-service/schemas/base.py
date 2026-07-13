from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """
    Base schema for all Pydantic models.
    """

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )