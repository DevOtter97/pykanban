"""SQLAlchemy ORM models — internal to the repository layer."""

from sqlalchemy import Boolean, Column as Col, ForeignKey, Integer, String, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class UserRow(Base):
    __tablename__ = "users"

    id              = Col(Integer, primary_key=True, index=True)
    email           = Col(String, unique=True, index=True, nullable=False)
    username        = Col(String, unique=True, index=True, nullable=False)
    hashed_password = Col(String, nullable=False)
    role            = Col(String, nullable=False, default="user")
    created_at      = Col(DateTime(timezone=True), server_default=func.now())

    team_memberships = relationship("TeamMemberRow", back_populates="user", cascade="all, delete")


class TeamRow(Base):
    __tablename__ = "teams"

    id          = Col(Integer, primary_key=True, index=True)
    name        = Col(String, unique=True, nullable=False)
    description = Col(String, nullable=True)
    created_at  = Col(DateTime(timezone=True), server_default=func.now())

    members  = relationship("TeamMemberRow", back_populates="team", cascade="all, delete")
    projects = relationship("ProjectRow", back_populates="team", cascade="all, delete")


class TeamMemberRow(Base):
    __tablename__ = "team_members"

    id      = Col(Integer, primary_key=True, index=True)
    team_id = Col(Integer, ForeignKey("teams.id"), nullable=False)
    user_id = Col(Integer, ForeignKey("users.id"), nullable=False)
    role    = Col(String, nullable=False, default="member")

    team = relationship("TeamRow", back_populates="members")
    user = relationship("UserRow", back_populates="team_memberships")


class ProjectRow(Base):
    __tablename__ = "projects"

    id          = Col(Integer, primary_key=True, index=True)
    title       = Col(String, nullable=False)
    description = Col(String, nullable=True)
    position    = Col(Integer, default=0)
    team_id     = Col(Integer, ForeignKey("teams.id"), nullable=True)
    owner_id    = Col(Integer, ForeignKey("users.id"), nullable=True)
    archived    = Col(Boolean, default=False, nullable=False)
    created_at  = Col(DateTime(timezone=True), server_default=func.now())

    team    = relationship("TeamRow", back_populates="projects")
    owner   = relationship("UserRow")
    columns = relationship("BoardColumnRow", back_populates="project", cascade="all, delete", order_by="BoardColumnRow.position")


class BoardColumnRow(Base):
    __tablename__ = "columns"

    id                     = Col(Integer, primary_key=True, index=True)
    title                  = Col(String, nullable=False)
    color                  = Col(String, default="#818cf8")
    position               = Col(Integer, default=0)
    owner_id               = Col(Integer, ForeignKey("users.id"), nullable=True)
    project_id             = Col(Integer, ForeignKey("projects.id"), nullable=True)
    is_mandatory           = Col(Boolean, default=False, nullable=False)
    is_visible_by_default  = Col(Boolean, default=True, nullable=False)
    created_at             = Col(DateTime(timezone=True), server_default=func.now())

    owner   = relationship("UserRow")
    project = relationship("ProjectRow", back_populates="columns")
    cards   = relationship("CardRow", back_populates="column", cascade="all, delete", order_by="CardRow.position")


class CategoryRow(Base):
    __tablename__ = "categories"

    id          = Col(Integer, primary_key=True, index=True)
    name        = Col(String, unique=True, nullable=False)
    description = Col(String, nullable=True)

    allowed_typologies = relationship("CategoryTypologyRow", back_populates="category")


class TypologyRow(Base):
    __tablename__ = "typologies"

    id          = Col(Integer, primary_key=True, index=True)
    name        = Col(String, unique=True, nullable=False)
    description = Col(String, nullable=True)

    allowed_categories = relationship("CategoryTypologyRow", back_populates="typology")


class CategoryTypologyRow(Base):
    __tablename__ = "category_typology"

    category_id = Col(Integer, ForeignKey("categories.id"), primary_key=True)
    typology_id = Col(Integer, ForeignKey("typologies.id"), primary_key=True)
    enabled     = Col(Boolean, nullable=False, default=True)

    category = relationship("CategoryRow", back_populates="allowed_typologies")
    typology = relationship("TypologyRow", back_populates="allowed_categories")


class CardRow(Base):
    __tablename__ = "cards"

    id               = Col(Integer, primary_key=True, index=True)
    title            = Col(String, nullable=False)
    description      = Col(String, nullable=True)
    position         = Col(Integer, default=0)
    column_id        = Col(Integer, ForeignKey("columns.id"), nullable=False)
    category_id      = Col(Integer, ForeignKey("categories.id"), nullable=True)
    typology_id      = Col(Integer, ForeignKey("typologies.id"), nullable=True)
    content          = Col(JSON, nullable=True)
    due_date         = Col(DateTime(timezone=True), nullable=True)
    assigned_to      = Col(Integer, ForeignKey("users.id"), nullable=True)
    completed_at     = Col(DateTime(timezone=True), nullable=True)
    completion_notes = Col(String, nullable=True)
    created_at       = Col(DateTime(timezone=True), server_default=func.now())
    updated_at       = Col(DateTime(timezone=True), onupdate=func.now())

    column   = relationship("BoardColumnRow", back_populates="cards")
    category = relationship("CategoryRow")
    typology = relationship("TypologyRow")
    assignee = relationship("UserRow", foreign_keys=[assigned_to])
