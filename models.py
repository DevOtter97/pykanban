"""SQLAlchemy ORM models for users, projects, columns, cards, categories, and typologies."""

from sqlalchemy import Boolean, Column as Col, ForeignKey, Integer, String, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class User(Base):
    """Application user with email/password authentication."""

    __tablename__ = "users"

    id              = Col(Integer, primary_key=True, index=True)
    email           = Col(String, unique=True, index=True, nullable=False)
    username        = Col(String, unique=True, index=True, nullable=False)
    hashed_password = Col(String, nullable=False)
    created_at      = Col(DateTime(timezone=True), server_default=func.now())

    projects = relationship("Project", back_populates="owner", cascade="all, delete")
    columns  = relationship("BoardColumn", back_populates="owner", cascade="all, delete")


class Project(Base):
    """Top-level container that groups board columns under a single owner."""

    __tablename__ = "projects"

    id          = Col(Integer, primary_key=True, index=True)
    title       = Col(String, nullable=False)
    description = Col(String, nullable=True)
    position    = Col(Integer, default=0)
    owner_id    = Col(Integer, ForeignKey("users.id"), nullable=False)
    created_at  = Col(DateTime(timezone=True), server_default=func.now())

    owner   = relationship("User", back_populates="projects")
    columns = relationship("BoardColumn", back_populates="project", cascade="all, delete", order_by="BoardColumn.position")


class BoardColumn(Base):
    """Kanban column belonging to a project (e.g. Pendiente, En progreso, Hecho)."""

    __tablename__ = "columns"

    id         = Col(Integer, primary_key=True, index=True)
    title      = Col(String, nullable=False)
    color      = Col(String, default="#818cf8")
    position   = Col(Integer, default=0)
    owner_id   = Col(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Col(Integer, ForeignKey("projects.id"), nullable=True)
    created_at = Col(DateTime(timezone=True), server_default=func.now())

    owner   = relationship("User", back_populates="columns")
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
    """Card typology / template (e.g. Desarrollo, Mantenimiento, Diseño)."""

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

    id          = Col(Integer, primary_key=True, index=True)
    title       = Col(String, nullable=False)
    description = Col(String, nullable=True)
    position    = Col(Integer, default=0)
    column_id   = Col(Integer, ForeignKey("columns.id"), nullable=False)
    category_id = Col(Integer, ForeignKey("categories.id"), nullable=True)
    typology_id = Col(Integer, ForeignKey("typologies.id"), nullable=True)
    content     = Col(JSON, nullable=True)
    due_date    = Col(DateTime(timezone=True), nullable=True)
    assigned_to = Col(Integer, ForeignKey("users.id"), nullable=True)
    created_at  = Col(DateTime(timezone=True), server_default=func.now())
    updated_at  = Col(DateTime(timezone=True), onupdate=func.now())

    column   = relationship("BoardColumn", back_populates="cards")
    category = relationship("Category")
    typology = relationship("Typology")
    assignee = relationship("User", foreign_keys=[assigned_to])
