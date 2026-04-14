"""Endpoints to manage the category ↔ typology check table."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Category, CategoryTypology, Typology, User
from schemas import CategoryTypologySet, CategoryTypologyResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/category-typology", tags=["category-typology"])


@router.get("/", response_model=list[CategoryTypologyResponse])
def list_mappings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all category ↔ typology mappings."""
    return db.query(CategoryTypology).all()


@router.put("/", response_model=CategoryTypologyResponse)
def set_mapping(
    data: CategoryTypologySet,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create or update a category ↔ typology mapping."""
    if not db.query(Category).filter(Category.id == data.category_id).first():
        raise HTTPException(status_code=404, detail="Category not found")
    if not db.query(Typology).filter(Typology.id == data.typology_id).first():
        raise HTTPException(status_code=404, detail="Typology not found")

    mapping = (
        db.query(CategoryTypology)
        .filter(
            CategoryTypology.category_id == data.category_id,
            CategoryTypology.typology_id == data.typology_id,
        )
        .first()
    )
    if mapping:
        mapping.enabled = data.enabled
    else:
        mapping = CategoryTypology(**data.model_dump())
        db.add(mapping)
    db.commit()
    db.refresh(mapping)
    logger.info(
        "category_typology_set",
        category_id=data.category_id,
        typology_id=data.typology_id,
        enabled=data.enabled,
    )
    return mapping
