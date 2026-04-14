"""SQLAlchemy implementation of ColumnRepository."""

from sqlalchemy.orm import Session

from models.column import ColumnOut
from repositories.sqlalchemy.db_models import BoardColumnRow


MANDATORY_COLUMNS = [
    {"title": "TO DO",       "color": "#64748b", "position": 0, "is_mandatory": True, "is_visible_by_default": True},
    {"title": "IN PROGRESS", "color": "#f59e0b", "position": 1, "is_mandatory": True, "is_visible_by_default": True},
    {"title": "DONE",        "color": "#10b981", "position": 2, "is_mandatory": True, "is_visible_by_default": True},
    {"title": "DESCARTADO",  "color": "#ef4444", "position": 3, "is_mandatory": True, "is_visible_by_default": False},
]


class SqlColumnRepository:
    def __init__(self, db: Session):
        self._db = db

    def get(self, column_id: int) -> ColumnOut | None:
        row = self._db.query(BoardColumnRow).filter(BoardColumnRow.id == column_id).first()
        return ColumnOut.model_validate(row) if row else None

    def list_by_project(self, project_id: int, *, include_hidden: bool = False) -> list[ColumnOut]:
        query = self._db.query(BoardColumnRow).filter(BoardColumnRow.project_id == project_id)
        if not include_hidden:
            query = query.filter(BoardColumnRow.is_visible_by_default == True)
        rows = query.order_by(BoardColumnRow.position).all()
        return [ColumnOut.model_validate(r) for r in rows]

    def create(self, *, title: str, color: str, position: int, project_id: int, owner_id: int | None = None, is_mandatory: bool = False, is_visible_by_default: bool = True) -> ColumnOut:
        row = BoardColumnRow(
            title=title, color=color, position=position,
            project_id=project_id, owner_id=owner_id,
            is_mandatory=is_mandatory, is_visible_by_default=is_visible_by_default,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return ColumnOut.model_validate(row)

    def update(self, column_id: int, updates: dict) -> ColumnOut | None:
        row = self._db.query(BoardColumnRow).filter(BoardColumnRow.id == column_id).first()
        if not row:
            return None
        for field, value in updates.items():
            setattr(row, field, value)
        self._db.commit()
        self._db.refresh(row)
        return ColumnOut.model_validate(row)

    def delete(self, column_id: int) -> bool:
        row = self._db.query(BoardColumnRow).filter(BoardColumnRow.id == column_id).first()
        if not row:
            return False
        self._db.delete(row)
        self._db.commit()
        return True

    def ensure_mandatory_columns(self, project_id: int, owner_id: int) -> None:
        existing = (
            self._db.query(BoardColumnRow)
            .filter(BoardColumnRow.project_id == project_id, BoardColumnRow.is_mandatory == True)
            .all()
        )
        existing_titles = {c.title for c in existing}
        for col_def in MANDATORY_COLUMNS:
            if col_def["title"] not in existing_titles:
                row = BoardColumnRow(**col_def, project_id=project_id, owner_id=owner_id)
                self._db.add(row)
        self._db.commit()
