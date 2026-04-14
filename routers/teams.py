"""CRUD endpoints for teams and team member management."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from models.user import UserOut
from models.team import TeamCreate, TeamUpdate, TeamOut, TeamListOut, TeamMemberAdd, TeamMemberUpdate, TeamMemberOut
from models.enums import TeamRoleEnum
from permissions import require_superadmin, require_team_admin, require_team_member
from repositories.protocols import TeamRepository, UserRepository
from repositories.sqlalchemy import get_team_repo, get_user_repo

logger = structlog.get_logger()

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("/", response_model=list[TeamListOut])
def list_teams(
    current_user: UserOut = Depends(get_current_user),
    team_repo: TeamRepository = Depends(get_team_repo),
):
    """List teams the user belongs to. Superadmins see all teams."""
    if current_user.role == "superadmin":
        return team_repo.list_all()
    return team_repo.list_by_user(current_user.id)


@router.post("/", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(
    data: TeamCreate,
    current_user: UserOut = Depends(get_current_user),
    team_repo: TeamRepository = Depends(get_team_repo),
):
    """Create a new team. Only superadmins can do this."""
    require_superadmin(current_user)
    if team_repo.name_exists(data.name):
        raise HTTPException(status_code=400, detail="Team name already taken")
    team = team_repo.create(name=data.name, description=data.description, creator_id=current_user.id)
    logger.info("team_created", team_id=team.id, name=team.name, user_id=current_user.id)
    return team


@router.get("/{team_id}", response_model=TeamOut)
def get_team(
    team_id: int,
    current_user: UserOut = Depends(get_current_user),
    team_repo: TeamRepository = Depends(get_team_repo),
):
    """Get team details. Must be a member or superadmin."""
    require_team_member(current_user, team_id, team_repo)
    team = team_repo.get(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.patch("/{team_id}", response_model=TeamOut)
def update_team(
    team_id: int,
    data: TeamUpdate,
    current_user: UserOut = Depends(get_current_user),
    team_repo: TeamRepository = Depends(get_team_repo),
):
    """Update team info. Only team admins or superadmins."""
    require_team_admin(current_user, team_id, team_repo)
    team = team_repo.update(team_id, data.model_dump(exclude_unset=True))
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    logger.info("team_updated", team_id=team_id, user_id=current_user.id)
    return team


# ── Member management ────────────────────────────────────────────────────────

@router.post("/{team_id}/members", response_model=TeamMemberOut, status_code=status.HTTP_201_CREATED)
def add_member(
    team_id: int,
    data: TeamMemberAdd,
    current_user: UserOut = Depends(get_current_user),
    team_repo: TeamRepository = Depends(get_team_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Add a user to the team. Only team admins or superadmins."""
    require_team_admin(current_user, team_id, team_repo)
    if not team_repo.get(team_id):
        raise HTTPException(status_code=404, detail="Team not found")
    if not user_repo.exists(data.user_id):
        raise HTTPException(status_code=404, detail="User not found")
    if team_repo.get_membership(data.user_id, team_id):
        raise HTTPException(status_code=400, detail="User is already a member of this team")
    if data.role not in (TeamRoleEnum.admin.value, TeamRoleEnum.member.value):
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'admin' or 'member'")
    member = team_repo.add_member(team_id=team_id, user_id=data.user_id, role=data.role)
    logger.info("member_added", team_id=team_id, user_id=data.user_id, role=data.role, by=current_user.id)
    return member


@router.patch("/{team_id}/members/{user_id}", response_model=TeamMemberOut)
def update_member_role(
    team_id: int,
    user_id: int,
    data: TeamMemberUpdate,
    current_user: UserOut = Depends(get_current_user),
    team_repo: TeamRepository = Depends(get_team_repo),
):
    """Change a member's role within the team. Only team admins or superadmins."""
    require_team_admin(current_user, team_id, team_repo)
    if data.role not in (TeamRoleEnum.admin.value, TeamRoleEnum.member.value):
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'admin' or 'member'")
    member = team_repo.update_member_role(team_id=team_id, user_id=user_id, role=data.role)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found in this team")
    logger.info("member_role_updated", team_id=team_id, user_id=user_id, new_role=data.role, by=current_user.id)
    return member


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    team_id: int,
    user_id: int,
    current_user: UserOut = Depends(get_current_user),
    team_repo: TeamRepository = Depends(get_team_repo),
):
    """Remove a member from the team. Only team admins or superadmins."""
    require_team_admin(current_user, team_id, team_repo)
    membership = team_repo.get_membership(user_id, team_id)
    if not membership:
        raise HTTPException(status_code=404, detail="Member not found in this team")
    if membership.role == TeamRoleEnum.admin.value:
        if team_repo.admin_count(team_id) <= 1:
            raise HTTPException(status_code=400, detail="Cannot remove the last admin of the team")
    team_repo.remove_member(team_id=team_id, user_id=user_id)
    logger.info("member_removed", team_id=team_id, user_id=user_id, by=current_user.id)
