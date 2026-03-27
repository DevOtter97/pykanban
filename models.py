from sqlalchemy import Column as Col, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class User(Base):
    __tablename__ = "users"

    id              = Col(Integer, primary_key=True, index=True)
    email           = Col(String, unique=True, index=True, nullable=False)
    username        = Col(String, unique=True, index=True, nullable=False)
    hashed_password = Col(String, nullable=False)
    created_at      = Col(DateTime(timezone=True), server_default=func.now())

    projects = relationship("Project", back_populates="owner", cascade="all, delete")
    columns  = relationship("BoardColumn", back_populates="owner", cascade="all, delete")


class Project(Base):
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
    tasks   = relationship("Task", back_populates="column", cascade="all, delete", order_by="Task.position")


class Task(Base):
    __tablename__ = "tasks"

    id          = Col(Integer, primary_key=True, index=True)
    title       = Col(String, nullable=False)
    description = Col(String, nullable=True)
    position    = Col(Integer, default=0)
    column_id   = Col(Integer, ForeignKey("columns.id"), nullable=False)
    due_date    = Col(DateTime(timezone=True), nullable=True)
    assigned_to = Col(Integer, ForeignKey("users.id"), nullable=True)
    created_at  = Col(DateTime(timezone=True), server_default=func.now())
    updated_at  = Col(DateTime(timezone=True), onupdate=func.now())

    column   = relationship("BoardColumn", back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assigned_to])
