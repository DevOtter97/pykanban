"""CRUD endpoints for cards, plus due-date queries, assignment, and state transitions."""

import structlog
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from models.user import UserOut
from models.card import CardCreate, CardUpdate, CardOut, CardMove
from permissions import require_project_access
from repositories.protocols import (
    CardRepository, ColumnRepository, ProjectRepository,
    TeamRepository, UserRepository, CategoryRepository,
    TypologyRepository, CategoryTypologyRepository,
)
from repositories.sqlalchemy import (
    get_card_repo, get_column_repo, get_project_repo,
    get_team_repo, get_user_repo, get_category_repo,
    get_typology_repo, get_cat_typ_repo,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/cards", tags=["cards"])


def _assert_column_accessible(col_id: int, user: UserOut, column_repo: ColumnRepository, project_repo: ProjectRepository, team_repo: TeamRepository):
    """Return the column if the user has access, otherwise raise 404."""
    col = column_repo.get(col_id)
    if not col:
        raise HTTPException(status_code=404, detail="Column not found")
    if col.project_id:
        require_project_access(user, col.project_id, project_repo, team_repo)
    elif col.owner_id and col.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Column not found")
    return col


def _get_card_with_access(card_id: int, user: UserOut, card_repo: CardRepository, column_repo: ColumnRepository, project_repo: ProjectRepository, team_repo: TeamRepository):
    """Return the card if the user has access, otherwise raise 404."""
    card = card_repo.get(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    col = column_repo.get(card.column_id)
    if col and col.project_id:
        require_project_access(user, col.project_id, project_repo, team_repo)
    elif col and col.owner_id and col.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Card not found")
    return card


def _assert_category_typology_allowed(category_id, typology_id, cat_repo: CategoryRepository, typ_repo: TypologyRepository, cat_typ_repo: CategoryTypologyRepository):
    """Validate that the category and typology exist and their combination is enabled."""
    if category_id is not None:
        if not cat_repo.exists(category_id):
            raise HTTPException(status_code=404, detail="Category not found")
    if typology_id is not None:
        if not typ_repo.exists(typology_id):
            raise HTTPException(status_code=404, detail="Typology not found")
    if category_id is not None and typology_id is not None:
        if not cat_typ_repo.is_combination_allowed(category_id, typology_id):
            raise HTTPException(status_code=400, detail="Category+typology combination not allowed")


@router.get("/due", response_model=list[CardOut])
def get_cards_by_due_date(
    overdue: bool = Query(False, description="Solo cards vencidas"),
    current_user: UserOut = Depends(get_current_user),
    card_repo: CardRepository = Depends(get_card_repo),
    project_repo: ProjectRepository = Depends(get_project_repo),
):
    """Devuelve cards con due_date asignada. Con ?overdue=true solo las vencidas."""
    if current_user.role == "superadmin":
        return card_repo.list_by_due_date(accessible_project_ids=None, owner_id=None, overdue=overdue)
    projects = project_repo.list_accessible(user_id=current_user.id, role=current_user.role)
    project_ids = [p.id for p in projects]
    return card_repo.list_by_due_date(accessible_project_ids=project_ids, owner_id=current_user.id, overdue=overdue)


@router.get("/mine", response_model=list[CardOut])
def get_my_cards(
    current_user: UserOut = Depends(get_current_user),
    card_repo: CardRepository = Depends(get_card_repo),
):
    """Cards asignadas al usuario autenticado."""
    return card_repo.list_by_assignee(current_user.id)


@router.post("/", response_model=CardOut, status_code=status.HTTP_201_CREATED)
def create_card(
    data: CardCreate,
    current_user: UserOut = Depends(get_current_user),
    card_repo: CardRepository = Depends(get_card_repo),
    column_repo: ColumnRepository = Depends(get_column_repo),
    project_repo: ProjectRepository = Depends(get_project_repo),
    team_repo: TeamRepository = Depends(get_team_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    cat_repo: CategoryRepository = Depends(get_category_repo),
    typ_repo: TypologyRepository = Depends(get_typology_repo),
    cat_typ_repo: CategoryTypologyRepository = Depends(get_cat_typ_repo),
):
    """Create a card. Any team member can create cards."""
    _assert_column_accessible(data.column_id, current_user, column_repo, project_repo, team_repo)
    if data.assigned_to is not None:
        if not user_repo.exists(data.assigned_to):
            raise HTTPException(status_code=404, detail="Assigned user not found")
    _assert_category_typology_allowed(data.category_id, data.typology_id, cat_repo, typ_repo, cat_typ_repo)
    card = card_repo.create(data.model_dump())
    logger.info("card_created", card_id=card.id, title=card.title, column_id=card.column_id, user_id=current_user.id)
    return card


@router.patch("/{card_id}", response_model=CardOut)
def update_card(
    card_id: int,
    data: CardUpdate,
    current_user: UserOut = Depends(get_current_user),
    card_repo: CardRepository = Depends(get_card_repo),
    column_repo: ColumnRepository = Depends(get_column_repo),
    project_repo: ProjectRepository = Depends(get_project_repo),
    team_repo: TeamRepository = Depends(get_team_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    cat_repo: CategoryRepository = Depends(get_category_repo),
    typ_repo: TypologyRepository = Depends(get_typology_repo),
    cat_typ_repo: CategoryTypologyRepository = Depends(get_cat_typ_repo),
):
    """Partially update a card. Any team member can update. Use POST /cards/{id}/move to change state."""
    card = _get_card_with_access(card_id, current_user, card_repo, column_repo, project_repo, team_repo)
    updates = data.model_dump(exclude_unset=True)
    if "assigned_to" in updates and updates["assigned_to"] is not None:
        if not user_repo.exists(updates["assigned_to"]):
            raise HTTPException(status_code=404, detail="Assigned user not found")
    new_cat = updates.get("category_id", card.category_id)
    new_typ = updates.get("typology_id", card.typology_id)
    if "category_id" in updates or "typology_id" in updates:
        _assert_category_typology_allowed(new_cat, new_typ, cat_repo, typ_repo, cat_typ_repo)
    updated = card_repo.update(card_id, updates)
    logger.info("card_updated", card_id=card_id, user_id=current_user.id)
    return updated


@router.post("/{card_id}/move", response_model=CardOut)
def move_card(
    card_id: int,
    data: CardMove,
    current_user: UserOut = Depends(get_current_user),
    card_repo: CardRepository = Depends(get_card_repo),
    column_repo: ColumnRepository = Depends(get_column_repo),
    project_repo: ProjectRepository = Depends(get_project_repo),
    team_repo: TeamRepository = Depends(get_team_repo),
):
    """Move a card to a different column (state change). Records completion date for DONE column."""
    card = _get_card_with_access(card_id, current_user, card_repo, column_repo, project_repo, team_repo)
    target_col = _assert_column_accessible(data.column_id, current_user, column_repo, project_repo, team_repo)

    old_column_id = card.column_id
    updates: dict = {"column_id": target_col.id}

    if target_col.title == "DONE":
        updates["completed_at"] = datetime.now(timezone.utc)
        if data.notes:
            updates["completion_notes"] = data.notes
    else:
        updates["completed_at"] = None
        updates["completion_notes"] = None

    if data.notes and target_col.title != "DONE":
        updates["completion_notes"] = data.notes

    updated = card_repo.update(card_id, updates)
    logger.info(
        "card_moved",
        card_id=card_id,
        from_column=old_column_id,
        to_column=target_col.id,
        to_title=target_col.title,
        user_id=current_user.id,
    )
    return updated


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(
    card_id: int,
    current_user: UserOut = Depends(get_current_user),
    card_repo: CardRepository = Depends(get_card_repo),
    column_repo: ColumnRepository = Depends(get_column_repo),
    project_repo: ProjectRepository = Depends(get_project_repo),
    team_repo: TeamRepository = Depends(get_team_repo),
):
    """Delete a card by ID. Any team member can delete cards."""
    _get_card_with_access(card_id, current_user, card_repo, column_repo, project_repo, team_repo)
    card_repo.delete(card_id)
    logger.info("card_deleted", card_id=card_id, user_id=current_user.id)
