"""SQLAlchemy implementation of ProjectRepository."""

from sqlalchemy.orm import Session

from models.project import ProjectOut
from repositories.sqlalchemy.db_models import ProjectRow, TeamMemberRow


class SqlProjectRepository:
    def __init__(self, db: Session):
        self._db = db

    def get(self, project_id: int) -> ProjectOut | None:
        row = self._db.query(ProjectRow).filter(ProjectRow.id == project_id).first()
        return ProjectOut.model_validate(row) if row else None

    def list_accessible(self, *, user_id: int, role: str, team_id: int | None = None) -> list[ProjectOut]:
        query = self._db.query(ProjectRow).filter(ProjectRow.archived == False)
        if team_id is not None:
            query = query.filter(ProjectRow.team_id == team_id)
        elif role != "superadmin":
            team_ids = (
                self._db.query(TeamMemberRow.team_id)
                .filter(TeamMemberRow.user_id == user_id)
                .scalar_subquery()
            )
            query = query.filter(
                (ProjectRow.team_id.in_(team_ids)) | (ProjectRow.owner_id == user_id)
            )
        return [ProjectOut.model_validate(r) for r in query.order_by(ProjectRow.position).all()]

    def create(self, *, title: str, description: str | None, position: int, team_id: int, owner_id: int) -> ProjectOut:
        row = ProjectRow(title=title, description=description, position=position, team_id=team_id, owner_id=owner_id)
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return ProjectOut.model_validate(row)

    def update(self, project_id: int, updates: dict) -> ProjectOut | None:
        row = self._db.query(ProjectRow).filter(ProjectRow.id == project_id).first()
        if not row:
            return None
        for field, value in updates.items():
            setattr(row, field, value)
        self._db.commit()
        self._db.refresh(row)
        return ProjectOut.model_validate(row)

    def set_archived(self, project_id: int, archived: bool) -> ProjectOut | None:
        row = self._db.query(ProjectRow).filter(ProjectRow.id == project_id).first()
        if not row:
            return None
        row.archived = archived
        self._db.commit()
        self._db.refresh(row)
        return ProjectOut.model_validate(row)
