"""Column domain models."""

from datetime import datetime
from pydantic import BaseModel, field_validator

from models.card import CardOut
from models.validators import validate_not_undefined


class ColumnCreate(BaseModel):
    title: str
    color: str = "#818cf8"
    position: int = 0
    project_id: int

    @field_validator("title")
    @classmethod
    def title_not_undefined(cls, v: str) -> str:
        return validate_not_undefined(v, "title")


class ColumnUpdate(BaseModel):
    title: str | None = None
    color: str | None = None
    position: int | None = None


class ColumnOut(BaseModel):
    id: int
    title: str
    color: str
    position: int
    project_id: int | None
    owner_id: int | None
    is_mandatory: bool
    is_visible_by_default: bool
    cards: list[CardOut] = []
    model_config = {"from_attributes": True}
