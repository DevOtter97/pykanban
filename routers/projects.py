"""CRUD endpoints for projects."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Project, User
from schemas import ProjectCreate, ProjectUpdate, ProjectResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/projects", tags=["projects"])


def own_project_or_404(project_id: int, user: User, db: Session) -> Project:
    """Return the project if it belongs to the user, otherwise raise 404."""
    p = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p


@router.get("/", response_model=list[ProjectResponse])
def list_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all projects owned by the authenticated user."""
    return (
        db.query(Project)
        .filter(Project.owner_id == current_user.id)
        .order_by(Project.position)
        .all()
    )


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new project for the authenticated user."""
    project = Project(**data.model_dump(), owner_id=current_user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    logger.info("project_created", project_id=project.id, title=project.title, user_id=current_user.id)
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Partially update a project. Only provided fields are changed."""
    project = own_project_or_404(project_id, current_user, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    logger.info("project_updated", project_id=project_id, user_id=current_user.id)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a project and its cascading columns/tasks."""
    project = own_project_or_404(project_id, current_user, db)
    db.delete(project)
    db.commit()
    logger.info("project_deleted", project_id=project_id, user_id=current_user.id)
