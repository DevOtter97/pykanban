"""CRUD endpoints for board columns, including mandatory column creation."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import BoardColumn, Project, User
from permissions import require_project_access, require_project_admin
from schemas import ColumnCreate, ColumnUpdate, ColumnResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/columns", tags=["columns"])

MANDATORY_COLUMNS = [
    {"title": "TO DO",        "color": "#64748b", "position": 0, "is_mandatory": True, "is_visible_by_default": True},
    {"title": "IN PROGRESS",  "color": "#f59e0b", "position": 1, "is_mandatory": True, "is_visible_by_default": True},
    {"title": "DONE",         "color": "#10b981", "position": 2, "is_mandatory": True, "is_visible_by_default": True},
    {"title": "DESCARTADO",   "color": "#ef4444", "position": 3, "is_mandatory": True, "is_visible_by_default": False},
]


def _ensure_mandatory_columns(project_id: int, owner_id: int, db: Session):
    """Create mandatory columns for a project if they don't exist yet."""
    existing = (
        db.query(BoardColumn)
        .filter(BoardColumn.project_id == project_id, BoardColumn.is_mandatory == True)
        .all()
    )
    existing_titles = {c.title for c in existing}
    for col_def in MANDATORY_COLUMNS:
        if col_def["title"] not in existing_titles:
            col = BoardColumn(**col_def, project_id=project_id, owner_id=owner_id)
            db.add(col)
    db.commit()


@router.get("/", response_model=list[ColumnResponse])
def list_columns(
    project_id: int,
    include_hidden: bool = Query(False, description="Include columns hidden by default (e.g. DESCARTADO)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List columns for a project. Creates mandatory columns on first access."""
    require_project_access(current_user, project_id, db)
    _ensure_mandatory_columns(project_id, current_user.id, db)
    query = (
        db.query(BoardColumn)
        .filter(BoardColumn.project_id == project_id)
    )
    if not include_hidden:
        query = query.filter(BoardColumn.is_visible_by_default == True)
    return query.order_by(BoardColumn.position).all()


@router.post("/", response_model=ColumnResponse, status_code=status.HTTP_201_CREATED)
def create_column(
    data: ColumnCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a custom column in the given project. Only team admins or superadmins."""
    require_project_admin(current_user, data.project_id, db)
    col = BoardColumn(**data.model_dump())
    db.add(col)
    db.commit()
    db.refresh(col)
    logger.info("column_created", column_id=col.id, title=col.title, project_id=data.project_id, user_id=current_user.id)
    return col


@router.patch("/{col_id}", response_model=ColumnResponse)
def update_column(
    col_id: int,
    data: ColumnUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Partially update a column. Only team admins or superadmins. Cannot rename mandatory columns."""
    col = db.query(BoardColumn).filter(BoardColumn.id == col_id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Column not found")
    require_project_admin(current_user, col.project_id, db)
    updates = data.model_dump(exclude_unset=True)
    if col.is_mandatory and "title" in updates:
        raise HTTPException(status_code=400, detail="Cannot rename mandatory columns")
    for field, value in updates.items():
        setattr(col, field, value)
    db.commit()
    db.refresh(col)
    logger.info("column_updated", column_id=col_id, user_id=current_user.id)
    return col


@router.delete("/{col_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_column(
    col_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a custom column. Mandatory columns cannot be deleted. Only team admins or superadmins."""
    col = db.query(BoardColumn).filter(BoardColumn.id == col_id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Column not found")
    require_project_admin(current_user, col.project_id, db)
    if col.is_mandatory:
        raise HTTPException(status_code=400, detail="Cannot delete mandatory columns")
    db.delete(col)
    db.commit()
    logger.info("column_deleted", column_id=col_id, user_id=current_user.id)
