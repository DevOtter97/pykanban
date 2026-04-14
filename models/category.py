"""Category domain models."""

from pydantic import BaseModel, field_validator

from models.validators import validate_not_undefined


class CategoryCreate(BaseModel):
    name: str
    description: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_undefined(cls, v: str) -> str:
        return validate_not_undefined(v, "name")


class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class CategoryOut(BaseModel):
    id: int
    name: str
    description: str | None
    model_config = {"from_attributes": True}
