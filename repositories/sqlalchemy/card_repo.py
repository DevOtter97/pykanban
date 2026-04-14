"""SQLAlchemy implementation of CardRepository."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models.card import CardOut
from repositories.sqlalchemy.db_models import CardRow, BoardColumnRow


class SqlCardRepository:
    def __init__(self, db: Session):
        self._db = db

    def get(self, card_id: int) -> CardOut | None:
        row = self._db.query(CardRow).filter(CardRow.id == card_id).first()
        return CardOut.model_validate(row) if row else None

    def get_column_id(self, card_id: int) -> int | None:
        row = self._db.query(CardRow.column_id).filter(CardRow.id == card_id).first()
        return row[0] if row else None

    def list_by_due_date(self, *, accessible_project_ids: list[int] | None, owner_id: int | None, overdue: bool = False) -> list[CardOut]:
        query = (
            self._db.query(CardRow)
            .join(BoardColumnRow)
            .filter(CardRow.due_date.isnot(None))
        )
        if accessible_project_ids is not None:
            conditions = BoardColumnRow.project_id.in_(accessible_project_ids)
            if owner_id is not None:
                conditions = conditions | (BoardColumnRow.owner_id == owner_id)
            query = query.filter(conditions)
        if overdue:
            query = query.filter(CardRow.due_date < datetime.now(timezone.utc))
        rows = query.order_by(CardRow.due_date).all()
        return [CardOut.model_validate(r) for r in rows]

    def list_by_assignee(self, user_id: int) -> list[CardOut]:
        rows = (
            self._db.query(CardRow)
            .filter(CardRow.assigned_to == user_id)
            .order_by(CardRow.position)
            .all()
        )
        return [CardOut.model_validate(r) for r in rows]

    def create(self, data: dict) -> CardOut:
        row = CardRow(**data)
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return CardOut.model_validate(row)

    def update(self, card_id: int, updates: dict) -> CardOut | None:
        row = self._db.query(CardRow).filter(CardRow.id == card_id).first()
        if not row:
            return None
        for field, value in updates.items():
            setattr(row, field, value)
        self._db.commit()
        self._db.refresh(row)
        return CardOut.model_validate(row)

    def delete(self, card_id: int) -> bool:
        row = self._db.query(CardRow).filter(CardRow.id == card_id).first()
        if not row:
            return False
        self._db.delete(row)
        self._db.commit()
        return True
