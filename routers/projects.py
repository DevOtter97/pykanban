"""CRUD endpoints for projects with team-based ownership and role permissions."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from models.user import UserOut
from models.project import ProjectCreate, ProjectUpdate, ProjectOut
from permissions import require_team_admin, require_team_member, require_project_admin
from repositories.protocols import ProjectRepository, TeamRepository
from repositories.sqlalchemy import get_project_repo, get_team_repo

logger = structlog.get_logger()

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=list[ProjectOut])
def list_projects(
    team_id: int | None = None,
    current_user: UserOut = Depends(get_current_user),
    project_repo: ProjectRepository = Depends(get_project_repo),
    team_repo: TeamRepository = Depends(get_team_repo),
):
    """List projects. Filter by team_id. Shows non-archived projects the user has access to."""
    if team_id is not None:
        require_team_member(current_user, team_id, team_repo)
    return project_repo.list_accessible(user_id=current_user.id, role=current_user.role, team_id=team_id)


@router.post("/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    data: ProjectCreate,
    current_user: UserOut = Depends(get_current_user),
    project_repo: ProjectRepository = Depends(get_project_repo),
    team_repo: TeamRepository = Depends(get_team_repo),
):
    """Create a new project linked to a team. Only team admins or superadmins."""
    if not team_repo.get(data.team_id):
        raise HTTPException(status_code=404, detail="Team not found")
    require_team_admin(current_user, data.team_id, team_repo)
    project = project_repo.create(
        title=data.title,
        description=data.description,
        position=data.position,
        team_id=data.team_id,
        owner_id=current_user.id,
    )
    logger.info("project_created", project_id=project.id, title=project.title, team_id=data.team_id, user_id=current_user.id)
    return project


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    data: ProjectUpdate,
    current_user: UserOut = Depends(get_current_user),
    project_repo: ProjectRepository = Depends(get_project_repo),
    team_repo: TeamRepository = Depends(get_team_repo),
):
    """Partially update a project. Only team admins or superadmins."""
    require_project_admin(current_user, project_id, project_repo, team_repo)
    project = project_repo.update(project_id, data.model_dump(exclude_unset=True))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    logger.info("project_updated", project_id=project_id, user_id=current_user.id)
    return project


@router.post("/{project_id}/archive", response_model=ProjectOut)
def archive_project(
    project_id: int,
    current_user: UserOut = Depends(get_current_user),
    project_repo: ProjectRepository = Depends(get_project_repo),
    team_repo: TeamRepository = Depends(get_team_repo),
):
    """Archive a project. Only team admins or superadmins. Projects cannot be deleted."""
    require_project_admin(current_user, project_id, project_repo, team_repo)
    project = project_repo.set_archived(project_id, True)
    logger.info("project_archived", project_id=project_id, user_id=current_user.id)
    return project


@router.post("/{project_id}/unarchive", response_model=ProjectOut)
def unarchive_project(
    project_id: int,
    current_user: UserOut = Depends(get_current_user),
    project_repo: ProjectRepository = Depends(get_project_repo),
    team_repo: TeamRepository = Depends(get_team_repo),
):
    """Restore an archived project. Only team admins or superadmins."""
    require_project_admin(current_user, project_id, project_repo, team_repo)
    project = project_repo.set_archived(project_id, False)
    logger.info("project_unarchived", project_id=project_id, user_id=current_user.id)
    return project
