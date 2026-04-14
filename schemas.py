"""Pydantic schemas for request validation and response serialization."""

from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime


FORBIDDEN_STRINGS = {"undefined", "null", "none", ""}


def _validate_not_undefined(v: str, field_name: str) -> str:
    if v.strip().lower() in FORBIDDEN_STRINGS:
        raise ValueError(f"{field_name} cannot be empty or undefined")
    return v


# ── User ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def username_not_undefined(cls, v: str) -> str:
        return _validate_not_undefined(v, "username")

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    role: str
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Team ──────────────────────────────────────────────────────────────────────

class TeamCreate(BaseModel):
    name: str
    description: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_undefined(cls, v: str) -> str:
        return _validate_not_undefined(v, "name")

class TeamUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

class TeamMemberAdd(BaseModel):
    user_id: int
    role: str = "member"

class TeamMemberUpdate(BaseModel):
    role: str

class TeamMemberResponse(BaseModel):
    id: int
    user_id: int
    role: str
    user: UserResponse
    model_config = {"from_attributes": True}

class TeamResponse(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime
    members: list[TeamMemberResponse] = []
    model_config = {"from_attributes": True}

class TeamListResponse(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Project ───────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    title: str
    description: str | None = None
    position: int = 0
    team_id: int

    @field_validator("title")
    @classmethod
    def title_not_undefined(cls, v: str) -> str:
        return _validate_not_undefined(v, "title")

class ProjectUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    position: int | None = None

class ProjectResponse(BaseModel):
    id: int
    title: str
    description: str | None
    position: int
    team_id: int | None
    archived: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Column ────────────────────────────────────────────────────────────────────

class ColumnCreate(BaseModel):
    title: str
    color: str = "#818cf8"
    position: int = 0
    project_id: int

    @field_validator("title")
    @classmethod
    def title_not_undefined(cls, v: str) -> str:
        return _validate_not_undefined(v, "title")

class ColumnUpdate(BaseModel):
    title: str | None = None
    color: str | None = None
    position: int | None = None


# ── Category ──────────────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    name: str
    description: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_undefined(cls, v: str) -> str:
        return _validate_not_undefined(v, "name")

class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str | None
    model_config = {"from_attributes": True}


# ── Typology ──────────────────────────────────────────────────────────────────

class TypologyCreate(BaseModel):
    name: str
    description: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_undefined(cls, v: str) -> str:
        return _validate_not_undefined(v, "name")

class TypologyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

class TypologyResponse(BaseModel):
    id: int
    name: str
    description: str | None
    model_config = {"from_attributes": True}


# ── CategoryTypology ─────────────────────────────────────────────────────────

class CategoryTypologySet(BaseModel):
    category_id: int
    typology_id: int
    enabled: bool

class CategoryTypologyResponse(BaseModel):
    category_id: int
    typology_id: int
    enabled: bool
    category: CategoryResponse
    typology: TypologyResponse
    model_config = {"from_attributes": True}


# ── Card ──────────────────────────────────────────────────────────────────────

class AssigneeResponse(BaseModel):
    id: int
    username: str
    model_config = {"from_attributes": True}

class CardResponse(BaseModel):
    id: int
    title: str
    description: str | None
    position: int
    column_id: int
    category_id: int | None
    typology_id: int | None
    content: dict | None
    category: CategoryResponse | None
    typology: TypologyResponse | None
    due_date: datetime | None
    assigned_to: int | None
    assignee: AssigneeResponse | None
    completed_at: datetime | None
    completion_notes: str | None
    created_at: datetime
    updated_at: datetime | None
    model_config = {"from_attributes": True}

class ColumnResponse(BaseModel):
    id: int
    title: str
    color: str
    position: int
    project_id: int | None
    is_mandatory: bool
    is_visible_by_default: bool
    cards: list[CardResponse] = []
    model_config = {"from_attributes": True}

class CardCreate(BaseModel):
    title: str
    description: str | None = None
    position: int = 0
    column_id: int

    @field_validator("title")
    @classmethod
    def title_not_undefined(cls, v: str) -> str:
        return _validate_not_undefined(v, "title")
    category_id: int | None = None
    typology_id: int | None = None
    content: dict | None = None
    due_date: datetime | None = None
    assigned_to: int | None = None

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


# ── Auth ──────────────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None
