"""SQLAlchemy implementation of CategoryRepository."""

from sqlalchemy.orm import Session

from models.category import CategoryOut
from repositories.sqlalchemy.db_models import CategoryRow


class SqlCategoryRepository:
    def __init__(self, db: Session):
        self._db = db

    def get(self, category_id: int) -> CategoryOut | None:
        row = self._db.query(CategoryRow).filter(CategoryRow.id == category_id).first()
        return CategoryOut.model_validate(row) if row else None

    def list_all(self) -> list[CategoryOut]:
        rows = self._db.query(CategoryRow).all()
        return [CategoryOut.model_validate(r) for r in rows]

    def create(self, *, name: str, description: str | None) -> CategoryOut:
        row = CategoryRow(name=name, description=description)
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return CategoryOut.model_validate(row)

    def update(self, category_id: int, updates: dict) -> CategoryOut | None:
        row = self._db.query(CategoryRow).filter(CategoryRow.id == category_id).first()
        if not row:
            return None
        for field, value in updates.items():
            setattr(row, field, value)
        self._db.commit()
        self._db.refresh(row)
        return CategoryOut.model_validate(row)

    def delete(self, category_id: int) -> bool:
        row = self._db.query(CategoryRow).filter(CategoryRow.id == category_id).first()
        if not row:
            return False
        self._db.delete(row)
        self._db.commit()
        return True

    def name_exists(self, name: str) -> bool:
        return self._db.query(CategoryRow).filter(CategoryRow.name == name).first() is not None

    def exists(self, category_id: int) -> bool:
        return self._db.query(CategoryRow).filter(CategoryRow.id == category_id).first() is not None
