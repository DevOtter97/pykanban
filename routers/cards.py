"""CRUD endpoints for cards, plus due-date and assignment queries."""

import structlog
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import BoardColumn, Card, User
from schemas import CardCreate, CardUpdate, CardResponse

logger = structlog.get_logger()


def assert_user_exists(user_id: int, db: Session):
    """Raise 404 if no user with the given ID exists."""
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="Assigned user not found")

router = APIRouter(prefix="/cards", tags=["cards"])


def own_card_or_404(card_id: int, user: User, db: Session) -> Card:
    """Return the card if it belongs to the user (via column ownership), otherwise raise 404."""
    card = (
        db.query(Card)
        .join(BoardColumn)
        .filter(Card.id == card_id, BoardColumn.owner_id == user.id)
        .first()
    )
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return card


def assert_column_owned(col_id: int, user: User, db: Session):
    """Raise 404 if the column does not belong to the user."""
    col = db.query(BoardColumn).filter(BoardColumn.id == col_id, BoardColumn.owner_id == user.id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Column not found")


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
        .filter(BoardColumn.owner_id == current_user.id, Card.due_date.isnot(None))
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
    """Create a card in the specified column. Validates column ownership and assignee existence."""
    assert_column_owned(data.column_id, current_user, db)
    if data.assigned_to is not None:
        assert_user_exists(data.assigned_to, db)
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
    """Partially update a card. Validates column and assignee if changed."""
    card = own_card_or_404(card_id, current_user, db)
    updates = data.model_dump(exclude_unset=True)
    if "column_id" in updates:
        assert_column_owned(updates["column_id"], current_user, db)
    if "assigned_to" in updates and updates["assigned_to"] is not None:
        assert_user_exists(updates["assigned_to"], db)
    for field, value in updates.items():
        setattr(card, field, value)
    db.commit()
    db.refresh(card)
    logger.info("card_updated", card_id=card_id, user_id=current_user.id)
    return card


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(
    card_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a card by ID."""
    card = own_card_or_404(card_id, current_user, db)
    db.delete(card)
    db.commit()
    logger.info("card_deleted", card_id=card_id, user_id=current_user.id)
