"""Card domain models."""

from datetime import datetime
from pydantic import BaseModel, field_validator

from models.category import CategoryOut
from models.typology import TypologyOut
from models.user import AssigneeOut
from models.validators import validate_not_undefined


class CardCreate(BaseModel):
    title: str
    description: str | None = None
    position: int = 0
    column_id: int
    category_id: int | None = None
    typology_id: int | None = None
    content: dict | None = None
    due_date: datetime | None = None
    assigned_to: int | None = None

    @field_validator("title")
    @classmethod
    def title_not_undefined(cls, v: str) -> str:
        return validate_not_undefined(v, "title")


class CardUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    position: int | None = None
    category_id: int | None = None
    typology_id: int | None = None
    content: dict | None = None
    due_date: datetime | None = None
    assigned_to: int | None = None


class CardMove(BaseModel):
    column_id: int
    notes: str | None = None


class CardOut(BaseModel):
    id: int
    title: str
    description: str | None
    position: int
    column_id: int
    category_id: int | None
    typology_id: int | None
    content: dict | None
    category: CategoryOut | None
    typology: TypologyOut | None
    due_date: datetime | None
    assigned_to: int | None
    assignee: AssigneeOut | None
    completed_at: datetime | None
    completion_notes: str | None
    created_at: datetime
    updated_at: datetime | None
    model_config = {"from_attributes": True}
