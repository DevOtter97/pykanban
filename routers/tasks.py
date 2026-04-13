"""CRUD endpoints for tasks, plus due-date and assignment queries."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import BoardColumn, Task, User
from schemas import TaskCreate, TaskUpdate, TaskResponse


def assert_user_exists(user_id: int, db: Session):
    """Raise 404 if no user with the given ID exists."""
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="Assigned user not found")

router = APIRouter(prefix="/tasks", tags=["tasks"])


def own_task_or_404(task_id: int, user: User, db: Session) -> Task:
    """Return the task if it belongs to the user (via column ownership), otherwise raise 404."""
    task = (
        db.query(Task)
        .join(BoardColumn)
        .filter(Task.id == task_id, BoardColumn.owner_id == user.id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def assert_column_owned(col_id: int, user: User, db: Session):
    """Raise 404 if the column does not belong to the user."""
    col = db.query(BoardColumn).filter(BoardColumn.id == col_id, BoardColumn.owner_id == user.id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Column not found")


@router.get("/due", response_model=list[TaskResponse])
def get_tasks_by_due_date(
    overdue: bool = Query(False, description="Solo tareas vencidas"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Devuelve tareas con due_date asignada. Con ?overdue=true solo las vencidas."""
    query = (
        db.query(Task)
        .join(BoardColumn)
        .filter(BoardColumn.owner_id == current_user.id, Task.due_date.isnot(None))
    )
    if overdue:
        query = query.filter(Task.due_date < datetime.now(timezone.utc))
    return query.order_by(Task.due_date).all()


@router.get("/mine", response_model=list[TaskResponse])
def get_my_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Tareas asignadas al usuario autenticado."""
    return (
        db.query(Task)
        .filter(Task.assigned_to == current_user.id)
        .order_by(Task.position)
        .all()
    )


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a task in the specified column. Validates column ownership and assignee existence."""
    assert_column_owned(data.column_id, current_user, db)
    if data.assigned_to is not None:
        assert_user_exists(data.assigned_to, db)
    task = Task(**data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Partially update a task. Validates column and assignee if changed."""
    task = own_task_or_404(task_id, current_user, db)
    updates = data.model_dump(exclude_unset=True)
    if "column_id" in updates:
        assert_column_owned(updates["column_id"], current_user, db)
    if "assigned_to" in updates and updates["assigned_to"] is not None:
        assert_user_exists(updates["assigned_to"], db)
    for field, value in updates.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a task by ID."""
    task = own_task_or_404(task_id, current_user, db)
    db.delete(task)
    db.commit()
