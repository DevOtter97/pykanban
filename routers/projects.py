"""CRUD endpoints for projects with team-based ownership and role permissions."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Project, User, RoleEnum
from permissions import (
    require_team_admin,
    require_team_member,
    require_project_access,
    require_project_admin,
    get_team_or_404,
)
from schemas import ProjectCreate, ProjectUpdate, ProjectResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=list[ProjectResponse])
def list_projects(
    team_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List projects. Filter by team_id. Shows non-archived projects the user has access to."""
    query = db.query(Project).filter(Project.archived == False)
    if team_id is not None:
        require_team_member(current_user, team_id, db)
        query = query.filter(Project.team_id == team_id)
    elif current_user.role == RoleEnum.superadmin.value:
        pass  # superadmins see all
    else:
        # Show projects from user's teams + legacy projects they own
        from models import TeamMember
        team_ids = (
            db.query(TeamMember.team_id)
            .filter(TeamMember.user_id == current_user.id)
            .subquery()
        )
        query = query.filter(
            (Project.team_id.in_(team_ids)) | (Project.owner_id == current_user.id)
        )
    return query.order_by(Project.position).all()


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new project linked to a team. Only team admins or superadmins."""
    get_team_or_404(data.team_id, db)
    require_team_admin(current_user, data.team_id, db)
    project = Project(**data.model_dump(), owner_id=current_user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    logger.info("project_created", project_id=project.id, title=project.title, team_id=data.team_id, user_id=current_user.id)
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Partially update a project. Only team admins or superadmins."""
    project = require_project_admin(current_user, project_id, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    logger.info("project_updated", project_id=project_id, user_id=current_user.id)
    return project


@router.post("/{project_id}/archive", response_model=ProjectResponse)
def archive_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Archive a project. Only team admins or superadmins. Projects cannot be deleted."""
    project = require_project_admin(current_user, project_id, db)
    project.archived = True
    db.commit()
    db.refresh(project)
    logger.info("project_archived", project_id=project_id, user_id=current_user.id)
    return project


@router.post("/{project_id}/unarchive", response_model=ProjectResponse)
def unarchive_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Restore an archived project. Only team admins or superadmins."""
    project = require_project_admin(current_user, project_id, db)
    project.archived = False
    db.commit()
    db.refresh(project)
    logger.info("project_unarchived", project_id=project_id, user_id=current_user.id)
    return project
