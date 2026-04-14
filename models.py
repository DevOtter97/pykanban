"""SQLAlchemy ORM models for users, teams, projects, columns, cards, categories, and typologies."""

from sqlalchemy import Boolean, Column as Col, ForeignKey, Integer, String, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from database import Base


class RoleEnum(str, enum.Enum):
    superadmin = "superadmin"
    user = "user"


class TeamRoleEnum(str, enum.Enum):
    admin = "admin"
    member = "member"


class User(Base):
    """Application user with email/password authentication and global role."""

    __tablename__ = "users"

    id              = Col(Integer, primary_key=True, index=True)
    email           = Col(String, unique=True, index=True, nullable=False)
    username        = Col(String, unique=True, index=True, nullable=False)
    hashed_password = Col(String, nullable=False)
    role            = Col(String, nullable=False, default=RoleEnum.user.value)
    created_at      = Col(DateTime(timezone=True), server_default=func.now())

    team_memberships = relationship("TeamMember", back_populates="user", cascade="all, delete")


class Team(Base):
    """A team groups users and owns projects."""

    __tablename__ = "teams"

    id          = Col(Integer, primary_key=True, index=True)
    name        = Col(String, unique=True, nullable=False)
    description = Col(String, nullable=True)
    created_at  = Col(DateTime(timezone=True), server_default=func.now())

    members  = relationship("TeamMember", back_populates="team", cascade="all, delete")
    projects = relationship("Project", back_populates="team", cascade="all, delete")


class TeamMember(Base):
    """Association between a user and a team, with a role within that team."""

    __tablename__ = "team_members"

    id      = Col(Integer, primary_key=True, index=True)
    team_id = Col(Integer, ForeignKey("teams.id"), nullable=False)
    user_id = Col(Integer, ForeignKey("users.id"), nullable=False)
    role    = Col(String, nullable=False, default=TeamRoleEnum.member.value)

    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")


class Project(Base):
    """Top-level container that groups board columns, owned by a team."""

    __tablename__ = "projects"

    id          = Col(Integer, primary_key=True, index=True)
    title       = Col(String, nullable=False)
    description = Col(String, nullable=True)
    position    = Col(Integer, default=0)
    team_id     = Col(Integer, ForeignKey("teams.id"), nullable=True)
    owner_id    = Col(Integer, ForeignKey("users.id"), nullable=True)
    archived    = Col(Boolean, default=False, nullable=False)
    created_at  = Col(DateTime(timezone=True), server_default=func.now())

    team    = relationship("Team", back_populates="projects")
    owner   = relationship("User")
    columns = relationship("BoardColumn", back_populates="project", cascade="all, delete", order_by="BoardColumn.position")


class BoardColumn(Base):
    """Kanban column belonging to a project (e.g. TO DO, IN PROGRESS, DONE)."""

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

    owner   = relationship("User")
    project = relationship("Project", back_populates="columns")
    cards   = relationship("Card", back_populates="column", cascade="all, delete", order_by="Card.position")


class Category(Base):
    """Card category (e.g. Bug, Task, Sugerencia)."""

    __tablename__ = "categories"

    id          = Col(Integer, primary_key=True, index=True)
    name        = Col(String, unique=True, nullable=False)
    description = Col(String, nullable=True)

    allowed_typologies = relationship("CategoryTypology", back_populates="category")


class Typology(Base):
    """Card typology / template (e.g. Desarrollo, Mantenimiento, Diseno)."""

    __tablename__ = "typologies"

    id          = Col(Integer, primary_key=True, index=True)
    name        = Col(String, unique=True, nullable=False)
    description = Col(String, nullable=True)

    allowed_categories = relationship("CategoryTypology", back_populates="typology")


class CategoryTypology(Base):
    """Many-to-many check table: which category+typology combos are enabled."""

    __tablename__ = "category_typology"

    category_id = Col(Integer, ForeignKey("categories.id"), primary_key=True)
    typology_id = Col(Integer, ForeignKey("typologies.id"), primary_key=True)
    enabled     = Col(Boolean, nullable=False, default=True)

    category = relationship("Category", back_populates="allowed_typologies")
    typology = relationship("Typology", back_populates="allowed_categories")


class Card(Base):
    """Individual work item placed inside a board column."""

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

    column   = relationship("BoardColumn", back_populates="cards")
    category = relationship("Category")
    typology = relationship("Typology")
    assignee = relationship("User", foreign_keys=[assigned_to])
