"""CRUD endpoints for cards, plus due-date queries, assignment, and state transitions."""

import structlog
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import BoardColumn, Card, Category, CategoryTypology, Typology, User
from permissions import require_project_access, require_team_member
from schemas import CardCreate, CardUpdate, CardResponse, CardMove

logger = structlog.get_logger()


def assert_user_exists(user_id: int, db: Session):
    """Raise 404 if no user with the given ID exists."""
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="Assigned user not found")


def assert_category_typology_allowed(category_id: int | None, typology_id: int | None, db: Session):
    """Validate that the category and typology exist and their combination is enabled."""
    if category_id is not None:
        if not db.query(Category).filter(Category.id == category_id).first():
            raise HTTPException(status_code=404, detail="Category not found")
    if typology_id is not None:
        if not db.query(Typology).filter(Typology.id == typology_id).first():
            raise HTTPException(status_code=404, detail="Typology not found")
    if category_id is not None and typology_id is not None:
        mapping = (
            db.query(CategoryTypology)
            .filter(
                CategoryTypology.category_id == category_id,
                CategoryTypology.typology_id == typology_id,
                CategoryTypology.enabled == True,
            )
            .first()
        )
        if not mapping:
            raise HTTPException(status_code=400, detail="Category+typology combination not allowed")


router = APIRouter(prefix="/cards", tags=["cards"])


def _get_card_with_access(card_id: int, user: User, db: Session) -> Card:
    """Return the card if the user has access (via project team membership), otherwise raise 404."""
    card = db.query(Card).join(BoardColumn).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    col = card.column
    if col.project_id:
        require_project_access(user, col.project_id, db)
    elif col.owner_id and col.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Card not found")
    return card


def _assert_column_accessible(col_id: int, user: User, db: Session) -> BoardColumn:
    """Return the column if the user has access, otherwise raise 404."""
    col = db.query(BoardColumn).filter(BoardColumn.id == col_id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Column not found")
    if col.project_id:
        require_project_access(user, col.project_id, db)
    elif col.owner_id and col.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Column not found")
    return col


@router.get("/due", response_model=list[CardResponse])
def get_cards_by_due_date(
    overdue: bool = Query(False, description="Solo cards vencidas"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Devuelve cards con due_date asignada. Con ?overdue=true solo las vencidas."""
    query = (
        db.query(Card)
        .join(BoardColumn)
        .filter(Card.due_date.isnot(None))
    )
    # Filter by accessible columns (team membership or legacy ownership)
    if current_user.role != "superadmin":
        from models import TeamMember, Project
        team_ids = (
            db.query(TeamMember.team_id)
            .filter(TeamMember.user_id == current_user.id)
            .scalar_subquery()
        )
        project_ids = (
            db.query(Project.id)
            .filter((Project.team_id.in_(team_ids)) | (Project.owner_id == current_user.id))
            .scalar_subquery()
        )
        query = query.filter(
            (BoardColumn.project_id.in_(project_ids)) | (BoardColumn.owner_id == current_user.id)
        )
    if overdue:
        query = query.filter(Card.due_date < datetime.now(timezone.utc))
    return query.order_by(Card.due_date).all()


@router.get("/mine", response_model=list[CardResponse])
def get_my_cards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cards asignadas al usuario autenticado."""
    return (
        db.query(Card)
        .filter(Card.assigned_to == current_user.id)
        .order_by(Card.position)
        .all()
    )


@router.post("/", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
def create_card(
    data: CardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a card. Any team member can create cards."""
    _assert_column_accessible(data.column_id, current_user, db)
    if data.assigned_to is not None:
        assert_user_exists(data.assigned_to, db)
    assert_category_typology_allowed(data.category_id, data.typology_id, db)
    card = Card(**data.model_dump())
    db.add(card)
    db.commit()
    db.refresh(card)
    logger.info("card_created", card_id=card.id, title=card.title, column_id=card.column_id, user_id=current_user.id)
    return card


@router.patch("/{card_id}", response_model=CardResponse)
def update_card(
    card_id: int,
    data: CardUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Partially update a card. Any team member can update. Use POST /cards/{id}/move to change state."""
    card = _get_card_with_access(card_id, current_user, db)
    updates = data.model_dump(exclude_unset=True)
    if "assigned_to" in updates and updates["assigned_to"] is not None:
        assert_user_exists(updates["assigned_to"], db)
    new_cat = updates.get("category_id", card.category_id)
    new_typ = updates.get("typology_id", card.typology_id)
    if "category_id" in updates or "typology_id" in updates:
        assert_category_typology_allowed(new_cat, new_typ, db)
    for field, value in updates.items():
        setattr(card, field, value)
    db.commit()
    db.refresh(card)
    logger.info("card_updated", card_id=card_id, user_id=current_user.id)
    return card


@router.post("/{card_id}/move", response_model=CardResponse)
def move_card(
    card_id: int,
    data: CardMove,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Move a card to a different column (state change). Records completion date for DONE column."""
    card = _get_card_with_access(card_id, current_user, db)
    target_col = _assert_column_accessible(data.column_id, current_user, db)

    old_column_id = card.column_id
    card.column_id = target_col.id

    # Record completion when moving to DONE
    if target_col.title == "DONE":
        card.completed_at = datetime.now(timezone.utc)
        if data.notes:
            card.completion_notes = data.notes
    else:
        # Clear completion data if moved away from DONE
        card.completed_at = None
        card.completion_notes = None

    # If notes provided and target is not DONE, still store them as completion_notes
    # (useful for DESCARTADO or other states where notes make sense)
    if data.notes and target_col.title != "DONE":
        card.completion_notes = data.notes

    db.commit()
    db.refresh(card)
    logger.info(
        "card_moved",
        card_id=card_id,
        from_column=old_column_id,
        to_column=target_col.id,
        to_title=target_col.title,
        user_id=current_user.id,
    )
    return card


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(
    card_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a card by ID. Any team member can delete cards."""
    card = _get_card_with_access(card_id, current_user, db)
    db.delete(card)
    db.commit()
    logger.info("card_deleted", card_id=card_id, user_id=current_user.id)
