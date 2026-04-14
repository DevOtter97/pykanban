"""SQLAlchemy implementation of TypologyRepository."""

from sqlalchemy.orm import Session

from models.typology import TypologyOut
from repositories.sqlalchemy.db_models import TypologyRow


class SqlTypologyRepository:
    def __init__(self, db: Session):
        self._db = db

    def get(self, typology_id: int) -> TypologyOut | None:
        row = self._db.query(TypologyRow).filter(TypologyRow.id == typology_id).first()
        return TypologyOut.model_validate(row) if row else None

    def list_all(self) -> list[TypologyOut]:
        rows = self._db.query(TypologyRow).all()
        return [TypologyOut.model_validate(r) for r in rows]

    def create(self, *, name: str, description: str | None) -> TypologyOut:
        row = TypologyRow(name=name, description=description)
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return TypologyOut.model_validate(row)

    def update(self, typology_id: int, updates: dict) -> TypologyOut | None:
        row = self._db.query(TypologyRow).filter(TypologyRow.id == typology_id).first()
        if not row:
            return None
        for field, value in updates.items():
            setattr(row, field, value)
        self._db.commit()
        self._db.refresh(row)
        return TypologyOut.model_validate(row)

    def delete(self, typology_id: int) -> bool:
        row = self._db.query(TypologyRow).filter(TypologyRow.id == typology_id).first()
        if not row:
            return False
        self._db.delete(row)
        self._db.commit()
        return True

    def name_exists(self, name: str) -> bool:
        return self._db.query(TypologyRow).filter(TypologyRow.name == name).first() is not None

    def exists(self, typology_id: int) -> bool:
        return self._db.query(TypologyRow).filter(TypologyRow.id == typology_id).first() is not None
