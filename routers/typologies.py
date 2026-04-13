"""CRUD endpoints for card typologies."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Typology, User
from schemas import TypologyCreate, TypologyUpdate, TypologyResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/typologies", tags=["typologies"])


@router.get("/", response_model=list[TypologyResponse])
def list_typologies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all typologies."""
    return db.query(Typology).all()


@router.post("/", response_model=TypologyResponse, status_code=status.HTTP_201_CREATED)
def create_typology(
    data: TypologyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new typology."""
    if db.query(Typology).filter(Typology.name == data.name).first():
        raise HTTPException(status_code=400, detail="Typology name already exists")
    typology = Typology(**data.model_dump())
    db.add(typology)
    db.commit()
    db.refresh(typology)
    logger.info("typology_created", typology_id=typology.id, name=typology.name)
    return typology


@router.patch("/{typology_id}", response_model=TypologyResponse)
def update_typology(
    typology_id: int,
    data: TypologyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a typology."""
    typology = db.query(Typology).filter(Typology.id == typology_id).first()
    if not typology:
        raise HTTPException(status_code=404, detail="Typology not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(typology, field, value)
    db.commit()
    db.refresh(typology)
    logger.info("typology_updated", typology_id=typology_id)
    return typology


@router.delete("/{typology_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_typology(
    typology_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a typology."""
    typology = db.query(Typology).filter(Typology.id == typology_id).first()
    if not typology:
        raise HTTPException(status_code=404, detail="Typology not found")
    db.delete(typology)
    db.commit()
    logger.info("typology_deleted", typology_id=typology_id)
