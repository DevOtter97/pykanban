"""CRUD endpoints for board columns, including mandatory column creation."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from models.user import UserOut
from models.column import ColumnCreate, ColumnUpdate, ColumnOut
from permissions import require_project_access, require_project_admin
from repositories.protocols import ColumnRepository, ProjectRepository, TeamRepository
from repositories.sqlalchemy import get_column_repo, get_project_repo, get_team_repo

logger = structlog.get_logger()

router = APIRouter(prefix="/columns", tags=["columns"])


@router.get("/", response_model=list[ColumnOut])
def list_columns(
    project_id: int,
    include_hidden: bool = Query(False, description="Include columns hidden by default (e.g. DESCARTADO)"),
    current_user: UserOut = Depends(get_current_user),
    column_repo: ColumnRepository = Depends(get_column_repo),
    project_repo: ProjectRepository = Depends(get_project_repo),
    team_repo: TeamRepository = Depends(get_team_repo),
):
    """List columns for a project. Creates mandatory columns on first access."""
    require_project_access(current_user, project_id, project_repo, team_repo)
    column_repo.ensure_mandatory_columns(project_id, current_user.id)
    return column_repo.list_by_project(project_id, include_hidden=include_hidden)


@router.post("/", response_model=ColumnOut, status_code=status.HTTP_201_CREATED)
def create_column(
    data: ColumnCreate,
    current_user: UserOut = Depends(get_current_user),
    column_repo: ColumnRepository = Depends(get_column_repo),
    project_repo: ProjectRepository = Depends(get_project_repo),
    team_repo: TeamRepository = Depends(get_team_repo),
):
    """Create a custom column in the given project. Only team admins or superadmins."""
    require_project_admin(current_user, data.project_id, project_repo, team_repo)
    col = column_repo.create(title=data.title, color=data.color, position=data.position, project_id=data.project_id)
    logger.info("column_created", column_id=col.id, title=col.title, project_id=data.project_id, user_id=current_user.id)
    return col


@router.patch("/{col_id}", response_model=ColumnOut)
def update_column(
    col_id: int,
    data: ColumnUpdate,
    current_user: UserOut = Depends(get_current_user),
    column_repo: ColumnRepository = Depends(get_column_repo),
    project_repo: ProjectRepository = Depends(get_project_repo),
    team_repo: TeamRepository = Depends(get_team_repo),
):
    """Partially update a column. Only team admins or superadmins. Cannot rename mandatory columns."""
    col = column_repo.get(col_id)
    if not col:
        raise HTTPException(status_code=404, detail="Column not found")
    require_project_admin(current_user, col.project_id, project_repo, team_repo)
    updates = data.model_dump(exclude_unset=True)
    if col.is_mandatory and "title" in updates:
        raise HTTPException(status_code=400, detail="Cannot rename mandatory columns")
    updated = column_repo.update(col_id, updates)
    logger.info("column_updated", column_id=col_id, user_id=current_user.id)
    return updated


@router.delete("/{col_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_column(
    col_id: int,
    current_user: UserOut = Depends(get_current_user),
    column_repo: ColumnRepository = Depends(get_column_repo),
    project_repo: ProjectRepository = Depends(get_project_repo),
    team_repo: TeamRepository = Depends(get_team_repo),
):
    """Delete a custom column. Mandatory columns cannot be deleted. Only team admins or superadmins."""
    col = column_repo.get(col_id)
    if not col:
        raise HTTPException(status_code=404, detail="Column not found")
    require_project_admin(current_user, col.project_id, project_repo, team_repo)
    if col.is_mandatory:
        raise HTTPException(status_code=400, detail="Cannot delete mandatory columns")
    column_repo.delete(col_id)
    logger.info("column_deleted", column_id=col_id, user_id=current_user.id)
