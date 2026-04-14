"""CRUD endpoints for teams and team member management."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Team, TeamMember, User, TeamRoleEnum
from permissions import (
    require_superadmin,
    get_team_or_404,
    require_team_admin,
    require_team_member,
)
from schemas import (
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamListResponse,
    TeamMemberAdd,
    TeamMemberUpdate,
    TeamMemberResponse,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("/", response_model=list[TeamListResponse])
def list_teams(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List teams the user belongs to. Superadmins see all teams."""
    if current_user.role == "superadmin":
        return db.query(Team).order_by(Team.name).all()
    team_ids = (
        db.query(TeamMember.team_id)
        .filter(TeamMember.user_id == current_user.id)
        .scalar_subquery()
    )
    return db.query(Team).filter(Team.id.in_(team_ids)).order_by(Team.name).all()


@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(
    data: TeamCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new team. Only superadmins can do this."""
    require_superadmin(current_user)
    if db.query(Team).filter(Team.name == data.name).first():
        raise HTTPException(status_code=400, detail="Team name already taken")
    team = Team(**data.model_dump())
    db.add(team)
    db.flush()
    logger.info("team_created", team_id=team.id, name=team.name, user_id=current_user.id)
    # Auto-add the creator as admin
    membership = TeamMember(team_id=team.id, user_id=current_user.id, role=TeamRoleEnum.admin.value)
    db.add(membership)
    db.commit()
    db.refresh(team)
    return team


@router.get("/{team_id}", response_model=TeamResponse)
def get_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get team details. Must be a member or superadmin."""
    require_team_member(current_user, team_id, db)
    return get_team_or_404(team_id, db)


@router.patch("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: int,
    data: TeamUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update team info. Only team admins or superadmins."""
    require_team_admin(current_user, team_id, db)
    team = get_team_or_404(team_id, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(team, field, value)
    db.commit()
    db.refresh(team)
    logger.info("team_updated", team_id=team_id, user_id=current_user.id)
    return team


# ── Member management ────────────────────────────────────────────────────────

@router.post("/{team_id}/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
def add_member(
    team_id: int,
    data: TeamMemberAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a user to the team. Only team admins or superadmins."""
    require_team_admin(current_user, team_id, db)
    get_team_or_404(team_id, db)
    if not db.query(User).filter(User.id == data.user_id).first():
        raise HTTPException(status_code=404, detail="User not found")
    existing = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == data.user_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member of this team")
    if data.role not in (TeamRoleEnum.admin.value, TeamRoleEnum.member.value):
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'admin' or 'member'")
    member = TeamMember(team_id=team_id, user_id=data.user_id, role=data.role)
    db.add(member)
    db.commit()
    db.refresh(member)
    logger.info("member_added", team_id=team_id, user_id=data.user_id, role=data.role, by=current_user.id)
    return member


@router.patch("/{team_id}/members/{user_id}", response_model=TeamMemberResponse)
def update_member_role(
    team_id: int,
    user_id: int,
    data: TeamMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change a member's role within the team. Only team admins or superadmins."""
    require_team_admin(current_user, team_id, db)
    member = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found in this team")
    if data.role not in (TeamRoleEnum.admin.value, TeamRoleEnum.member.value):
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'admin' or 'member'")
    member.role = data.role
    db.commit()
    db.refresh(member)
    logger.info("member_role_updated", team_id=team_id, user_id=user_id, new_role=data.role, by=current_user.id)
    return member


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    team_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a member from the team. Only team admins or superadmins."""
    require_team_admin(current_user, team_id, db)
    member = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found in this team")
    # Prevent removing the last admin
    if member.role == TeamRoleEnum.admin.value:
        admin_count = (
            db.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.role == TeamRoleEnum.admin.value)
            .count()
        )
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot remove the last admin of the team")
    db.delete(member)
    db.commit()
    logger.info("member_removed", team_id=team_id, user_id=user_id, by=current_user.id)
