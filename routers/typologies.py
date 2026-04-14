"""CRUD endpoints for card typologies."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from models.user import UserOut
from models.typology import TypologyCreate, TypologyUpdate, TypologyOut
from repositories.protocols import TypologyRepository
from repositories.sqlalchemy import get_typology_repo

logger = structlog.get_logger()

router = APIRouter(prefix="/typologies", tags=["typologies"])


@router.get("/", response_model=list[TypologyOut])
def list_typologies(
    current_user: UserOut = Depends(get_current_user),
    typ_repo: TypologyRepository = Depends(get_typology_repo),
):
    """List all typologies."""
    return typ_repo.list_all()


@router.post("/", response_model=TypologyOut, status_code=status.HTTP_201_CREATED)
def create_typology(
    data: TypologyCreate,
    current_user: UserOut = Depends(get_current_user),
    typ_repo: TypologyRepository = Depends(get_typology_repo),
):
    """Create a new typology."""
    if typ_repo.name_exists(data.name):
        raise HTTPException(status_code=400, detail="Typology name already exists")
    typology = typ_repo.create(name=data.name, description=data.description)
    logger.info("typology_created", typology_id=typology.id, name=typology.name)
    return typology


@router.patch("/{typology_id}", response_model=TypologyOut)
def update_typology(
    typology_id: int,
    data: TypologyUpdate,
    current_user: UserOut = Depends(get_current_user),
    typ_repo: TypologyRepository = Depends(get_typology_repo),
):
    """Update a typology."""
    typology = typ_repo.update(typology_id, data.model_dump(exclude_unset=True))
    if not typology:
        raise HTTPException(status_code=404, detail="Typology not found")
    logger.info("typology_updated", typology_id=typology_id)
    return typology


@router.delete("/{typology_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_typology(
    typology_id: int,
    current_user: UserOut = Depends(get_current_user),
    typ_repo: TypologyRepository = Depends(get_typology_repo),
):
    """Delete a typology."""
    if not typ_repo.delete(typology_id):
        raise HTTPException(status_code=404, detail="Typology not found")
    logger.info("typology_deleted", typology_id=typology_id)
