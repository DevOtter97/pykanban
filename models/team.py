"""Team domain models."""

from datetime import datetime
from pydantic import BaseModel, field_validator

from models.user import UserOut
from models.validators import validate_not_undefined


class TeamCreate(BaseModel):
    name: str
    description: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_undefined(cls, v: str) -> str:
        return validate_not_undefined(v, "name")


class TeamUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class TeamMemberAdd(BaseModel):
    user_id: int
    role: str = "member"


class TeamMemberUpdate(BaseModel):
    role: str


class TeamMemberOut(BaseModel):
    id: int
    user_id: int
    role: str
    user: UserOut
    model_config = {"from_attributes": True}


class TeamOut(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime
    members: list[TeamMemberOut] = []
    model_config = {"from_attributes": True}


class TeamListOut(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime
    model_config = {"from_attributes": True}
