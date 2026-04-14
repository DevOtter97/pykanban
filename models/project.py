"""Project domain models."""

from datetime import datetime
from pydantic import BaseModel, field_validator

from models.validators import validate_not_undefined


class ProjectCreate(BaseModel):
    title: str
    description: str | None = None
    position: int = 0
    team_id: int

    @field_validator("title")
    @classmethod
    def title_not_undefined(cls, v: str) -> str:
        return validate_not_undefined(v, "title")


class ProjectUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    position: int | None = None


class ProjectOut(BaseModel):
    id: int
    title: str
    description: str | None
    position: int
    team_id: int | None
    owner_id: int | None
    archived: bool
    created_at: datetime
    model_config = {"from_attributes": True}
