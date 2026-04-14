"""User domain models."""

from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator

from models.validators import validate_not_undefined


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def username_not_undefined(cls, v: str) -> str:
        return validate_not_undefined(v, "username")


class UserOut(BaseModel):
    id: int
    email: str
    username: str
    role: str
    created_at: datetime
    model_config = {"from_attributes": True}


class AssigneeOut(BaseModel):
    id: int
    username: str
    model_config = {"from_attributes": True}
