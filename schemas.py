from pydantic import BaseModel, EmailStr
from datetime import datetime


# ── User ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Project ───────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    title: str
    description: str | None = None
    position: int = 0

class ProjectUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    position: int | None = None

class ProjectResponse(BaseModel):
    id: int
    title: str
    description: str | None
    position: int
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Column ────────────────────────────────────────────────────────────────────

class ColumnCreate(BaseModel):
    title: str
    color: str = "#818cf8"
    position: int = 0
    project_id: int

class ColumnUpdate(BaseModel):
    title: str | None = None
    color: str | None = None
    position: int | None = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None
    position: int
    column_id: int
    created_at: datetime
    updated_at: datetime | None
    model_config = {"from_attributes": True}

class ColumnResponse(BaseModel):
    id: int
    title: str
    color: str
    position: int
    project_id: int | None
    tasks: list[TaskResponse] = []
    model_config = {"from_attributes": True}


# ── Task ──────────────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    position: int = 0
    column_id: int

class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    position: int | None = None
    column_id: int | None = None


# ── Auth ──────────────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None
