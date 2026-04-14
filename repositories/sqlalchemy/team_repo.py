"""SQLAlchemy implementation of TeamRepository."""

from sqlalchemy.orm import Session

from models.team import TeamOut, TeamListOut, TeamMemberOut
from models.enums import TeamRoleEnum
from repositories.sqlalchemy.db_models import TeamRow, TeamMemberRow


class SqlTeamRepository:
    def __init__(self, db: Session):
        self._db = db

    def get(self, team_id: int) -> TeamOut | None:
        row = self._db.query(TeamRow).filter(TeamRow.id == team_id).first()
        return TeamOut.model_validate(row) if row else None

    def list_all(self) -> list[TeamListOut]:
        rows = self._db.query(TeamRow).order_by(TeamRow.name).all()
        return [TeamListOut.model_validate(r) for r in rows]

    def list_by_user(self, user_id: int) -> list[TeamListOut]:
        team_ids = (
            self._db.query(TeamMemberRow.team_id)
            .filter(TeamMemberRow.user_id == user_id)
            .scalar_subquery()
        )
        rows = self._db.query(TeamRow).filter(TeamRow.id.in_(team_ids)).order_by(TeamRow.name).all()
        return [TeamListOut.model_validate(r) for r in rows]

    def create(self, *, name: str, description: str | None, creator_id: int) -> TeamOut:
        team = TeamRow(name=name, description=description)
        self._db.add(team)
        self._db.flush()
        membership = TeamMemberRow(team_id=team.id, user_id=creator_id, role=TeamRoleEnum.admin.value)
        self._db.add(membership)
        self._db.commit()
        self._db.refresh(team)
        return TeamOut.model_validate(team)

    def update(self, team_id: int, updates: dict) -> TeamOut | None:
        row = self._db.query(TeamRow).filter(TeamRow.id == team_id).first()
        if not row:
            return None
        for field, value in updates.items():
            setattr(row, field, value)
        self._db.commit()
        self._db.refresh(row)
        return TeamOut.model_validate(row)

    def name_exists(self, name: str) -> bool:
        return self._db.query(TeamRow).filter(TeamRow.name == name).first() is not None

    def get_membership(self, user_id: int, team_id: int) -> TeamMemberOut | None:
        row = (
            self._db.query(TeamMemberRow)
            .filter(TeamMemberRow.team_id == team_id, TeamMemberRow.user_id == user_id)
            .first()
        )
        return TeamMemberOut.model_validate(row) if row else None

    def add_member(self, *, team_id: int, user_id: int, role: str) -> TeamMemberOut:
        row = TeamMemberRow(team_id=team_id, user_id=user_id, role=role)
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return TeamMemberOut.model_validate(row)

    def update_member_role(self, *, team_id: int, user_id: int, role: str) -> TeamMemberOut | None:
        row = (
            self._db.query(TeamMemberRow)
            .filter(TeamMemberRow.team_id == team_id, TeamMemberRow.user_id == user_id)
            .first()
        )
        if not row:
            return None
        row.role = role
        self._db.commit()
        self._db.refresh(row)
        return TeamMemberOut.model_validate(row)

    def remove_member(self, *, team_id: int, user_id: int) -> bool:
        row = (
            self._db.query(TeamMemberRow)
            .filter(TeamMemberRow.team_id == team_id, TeamMemberRow.user_id == user_id)
            .first()
        )
        if not row:
            return False
        self._db.delete(row)
        self._db.commit()
        return True

    def admin_count(self, team_id: int) -> int:
        return (
            self._db.query(TeamMemberRow)
            .filter(TeamMemberRow.team_id == team_id, TeamMemberRow.role == TeamRoleEnum.admin.value)
            .count()
        )

    def list_user_team_ids(self, user_id: int) -> list[int]:
        rows = (
            self._db.query(TeamMemberRow.team_id)
            .filter(TeamMemberRow.user_id == user_id)
            .all()
        )
        return [r[0] for r in rows]
