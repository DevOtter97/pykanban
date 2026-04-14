"""Centralized permission helpers used across routers."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models import Project, Team, TeamMember, User, RoleEnum, TeamRoleEnum


def require_superadmin(user: User):
    """Raise 403 if the user is not a superadmin."""
    if user.role != RoleEnum.superadmin.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superadmins can perform this action",
        )


def get_team_or_404(team_id: int, db: Session) -> Team:
    """Return the team or raise 404."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


def get_team_membership(user: User, team_id: int, db: Session) -> TeamMember | None:
    """Return the user's membership in the team, or None."""
    return (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == user.id)
        .first()
    )


def require_team_member(user: User, team_id: int, db: Session) -> TeamMember:
    """Raise 403 if the user is not a member of the team. Superadmins bypass."""
    if user.role == RoleEnum.superadmin.value:
        membership = get_team_membership(user, team_id, db)
        if membership:
            return membership
        # Superadmin can act even without a membership record
        fake = TeamMember(team_id=team_id, user_id=user.id, role=TeamRoleEnum.admin.value)
        return fake
    membership = get_team_membership(user, team_id, db)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team",
        )
    return membership


def require_team_admin(user: User, team_id: int, db: Session) -> TeamMember:
    """Raise 403 if the user is not an admin of the team. Superadmins bypass."""
    if user.role == RoleEnum.superadmin.value:
        membership = get_team_membership(user, team_id, db)
        if membership:
            return membership
        fake = TeamMember(team_id=team_id, user_id=user.id, role=TeamRoleEnum.admin.value)
        return fake
    membership = get_team_membership(user, team_id, db)
    if not membership or membership.role != TeamRoleEnum.admin.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team admins can perform this action",
        )
    return membership


def get_project_or_404(project_id: int, db: Session) -> Project:
    """Return the project or raise 404."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def require_project_access(user: User, project_id: int, db: Session) -> Project:
    """Return the project if the user has access (member of the project's team or owner). Raise 403/404."""
    project = get_project_or_404(project_id, db)
    if user.role == RoleEnum.superadmin.value:
        return project
    # Legacy projects without team_id — check owner_id
    if project.team_id is None:
        if project.owner_id == user.id:
            return project
        raise HTTPException(status_code=404, detail="Project not found")
    require_team_member(user, project.team_id, db)
    return project


def require_project_admin(user: User, project_id: int, db: Session) -> Project:
    """Return the project if the user is admin of its team. Raise 403/404."""
    project = get_project_or_404(project_id, db)
    if user.role == RoleEnum.superadmin.value:
        return project
    if project.team_id is None:
        if project.owner_id == user.id:
            return project
        raise HTTPException(status_code=404, detail="Project not found")
    require_team_admin(user, project.team_id, db)
    return project
