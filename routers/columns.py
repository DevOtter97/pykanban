import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import BoardColumn, Project, User
from schemas import ColumnCreate, ColumnUpdate, ColumnResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/columns", tags=["columns"])

DEFAULT_COLUMNS = [
    {"title": "Pendiente",   "color": "#64748b", "position": 0},
    {"title": "En progreso", "color": "#f59e0b", "position": 1},
    {"title": "Hecho",       "color": "#10b981", "position": 2},
]


def own_column_or_404(col_id: int, user: User, db: Session) -> BoardColumn:
    col = db.query(BoardColumn).filter(BoardColumn.id == col_id, BoardColumn.owner_id == user.id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Column not found")
    return col


def own_project_or_404(project_id: int, user: User, db: Session) -> Project:
    p = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p


@router.get("/", response_model=list[ColumnResponse])
def list_columns(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    own_project_or_404(project_id, current_user, db)
    cols = (
        db.query(BoardColumn)
        .filter(BoardColumn.owner_id == current_user.id, BoardColumn.project_id == project_id)
        .order_by(BoardColumn.position)
        .all()
    )
    # Create default columns the first time a project is opened
    if not cols:
        logger.info("default_columns_created", project_id=project_id, user_id=current_user.id)
        cols = [BoardColumn(**c, owner_id=current_user.id, project_id=project_id) for c in DEFAULT_COLUMNS]
        db.add_all(cols)
        db.commit()
        for c in cols:
            db.refresh(c)
    return cols


@router.post("/", response_model=ColumnResponse, status_code=status.HTTP_201_CREATED)
def create_column(
    data: ColumnCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    own_project_or_404(data.project_id, current_user, db)
    col = BoardColumn(**data.model_dump(), owner_id=current_user.id)
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
    col = own_column_or_404(col_id, current_user, db)
    for field, value in data.model_dump(exclude_unset=True).items():
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
    col = own_column_or_404(col_id, current_user, db)
    db.delete(col)
    db.commit()
    logger.info("column_deleted", column_id=col_id, user_id=current_user.id)
