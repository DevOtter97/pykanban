"""SQLAlchemy implementation of UserRepository."""

from sqlalchemy.orm import Session

from models.user import UserOut
from repositories.sqlalchemy.db_models import UserRow


class SqlUserRepository:
    def __init__(self, db: Session):
        self._db = db

    def get_by_id(self, user_id: int) -> UserOut | None:
        row = self._db.query(UserRow).filter(UserRow.id == user_id).first()
        return UserOut.model_validate(row) if row else None

    def get_by_username(self, username: str) -> UserOut | None:
        row = self._db.query(UserRow).filter(UserRow.username == username).first()
        return UserOut.model_validate(row) if row else None

    def get_by_email(self, email: str) -> UserOut | None:
        row = self._db.query(UserRow).filter(UserRow.email == email).first()
        return UserOut.model_validate(row) if row else None

    def get_password_hash(self, username: str) -> str | None:
        row = self._db.query(UserRow).filter(UserRow.username == username).first()
        return row.hashed_password if row else None

    def create(self, *, email: str, username: str, hashed_password: str) -> UserOut:
        row = UserRow(email=email, username=username, hashed_password=hashed_password)
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return UserOut.model_validate(row)

    def exists(self, user_id: int) -> bool:
        return self._db.query(UserRow).filter(UserRow.id == user_id).first() is not None
