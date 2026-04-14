"""Centralized permission helpers used across routers."""

from fastapi import HTTPException, status

from models.user import UserOut
from models.enums import RoleEnum, TeamRoleEnum
from repositories.protocols import TeamRepository, ProjectRepository


def require_superadmin(user: UserOut):
    """Raise 403 if the user is not a superadmin."""
    if user.role != RoleEnum.superadmin.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superadmins can perform this action",
        )


def require_team_member(user: UserOut, team_id: int, team_repo: TeamRepository):
    """Raise 403 if the user is not a member of the team. Superadmins bypass."""
    if user.role == RoleEnum.superadmin.value:
        return
    membership = team_repo.get_membership(user.id, team_id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team",
        )


def require_team_admin(user: UserOut, team_id: int, team_repo: TeamRepository):
    """Raise 403 if the user is not an admin of the team. Superadmins bypass."""
    if user.role == RoleEnum.superadmin.value:
        return
    membership = team_repo.get_membership(user.id, team_id)
    if not membership or membership.role != TeamRoleEnum.admin.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team admins can perform this action",
        )


def require_project_access(user: UserOut, project_id: int, project_repo: ProjectRepository, team_repo: TeamRepository):
    """Return the project if the user has access. Raise 403/404."""
    project = project_repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if user.role == RoleEnum.superadmin.value:
        return project
    if project.team_id is None:
        if project.owner_id == user.id:
            return project
        raise HTTPException(status_code=404, detail="Project not found")
    require_team_member(user, project.team_id, team_repo)
    return project


def require_project_admin(user: UserOut, project_id: int, project_repo: ProjectRepository, team_repo: TeamRepository):
    """Return the project if the user is admin of its team. Raise 403/404."""
    project = project_repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if user.role == RoleEnum.superadmin.value:
        return project
    if project.team_id is None:
        if project.owner_id == user.id:
            return project
        raise HTTPException(status_code=404, detail="Project not found")
    require_team_admin(user, project.team_id, team_repo)
    return project
