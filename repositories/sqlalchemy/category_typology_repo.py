"""SQLAlchemy implementation of CategoryTypologyRepository."""

from sqlalchemy.orm import Session

from models.category_typology import CategoryTypologyOut
from repositories.sqlalchemy.db_models import CategoryTypologyRow


class SqlCategoryTypologyRepository:
    def __init__(self, db: Session):
        self._db = db

    def list_all(self) -> list[CategoryTypologyOut]:
        rows = self._db.query(CategoryTypologyRow).all()
        return [CategoryTypologyOut.model_validate(r) for r in rows]

    def set_mapping(self, *, category_id: int, typology_id: int, enabled: bool) -> CategoryTypologyOut:
        row = (
            self._db.query(CategoryTypologyRow)
            .filter(
                CategoryTypologyRow.category_id == category_id,
                CategoryTypologyRow.typology_id == typology_id,
            )
            .first()
        )
        if row:
            row.enabled = enabled
        else:
            row = CategoryTypologyRow(category_id=category_id, typology_id=typology_id, enabled=enabled)
            self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return CategoryTypologyOut.model_validate(row)

    def is_combination_allowed(self, category_id: int, typology_id: int) -> bool:
        row = (
            self._db.query(CategoryTypologyRow)
            .filter(
                CategoryTypologyRow.category_id == category_id,
                CategoryTypologyRow.typology_id == typology_id,
                CategoryTypologyRow.enabled == True,
            )
            .first()
        )
        return row is not None
