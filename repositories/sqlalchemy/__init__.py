"""SQLAlchemy repository implementations and FastAPI dependency providers."""

from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from repositories.sqlalchemy.user_repo import SqlUserRepository
from repositories.sqlalchemy.team_repo import SqlTeamRepository
from repositories.sqlalchemy.project_repo import SqlProjectRepository
from repositories.sqlalchemy.column_repo import SqlColumnRepository
from repositories.sqlalchemy.card_repo import SqlCardRepository
from repositories.sqlalchemy.category_repo import SqlCategoryRepository
from repositories.sqlalchemy.typology_repo import SqlTypologyRepository
from repositories.sqlalchemy.category_typology_repo import SqlCategoryTypologyRepository


def get_user_repo(db: Session = Depends(get_db)) -> SqlUserRepository:
    return SqlUserRepository(db)


def get_team_repo(db: Session = Depends(get_db)) -> SqlTeamRepository:
    return SqlTeamRepository(db)


def get_project_repo(db: Session = Depends(get_db)) -> SqlProjectRepository:
    return SqlProjectRepository(db)


def get_column_repo(db: Session = Depends(get_db)) -> SqlColumnRepository:
    return SqlColumnRepository(db)


def get_card_repo(db: Session = Depends(get_db)) -> SqlCardRepository:
    return SqlCardRepository(db)


def get_category_repo(db: Session = Depends(get_db)) -> SqlCategoryRepository:
    return SqlCategoryRepository(db)


def get_typology_repo(db: Session = Depends(get_db)) -> SqlTypologyRepository:
    return SqlTypologyRepository(db)


def get_cat_typ_repo(db: Session = Depends(get_db)) -> SqlCategoryTypologyRepository:
    return SqlCategoryTypologyRepository(db)
