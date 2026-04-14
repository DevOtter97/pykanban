"""Endpoints to manage the category ↔ typology check table."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from models.user import UserOut
from models.category_typology import CategoryTypologySet, CategoryTypologyOut
from repositories.protocols import CategoryRepository, TypologyRepository, CategoryTypologyRepository
from repositories.sqlalchemy import get_category_repo, get_typology_repo, get_cat_typ_repo

logger = structlog.get_logger()

router = APIRouter(prefix="/category-typology", tags=["category-typology"])


@router.get("/", response_model=list[CategoryTypologyOut])
def list_mappings(
    current_user: UserOut = Depends(get_current_user),
    cat_typ_repo: CategoryTypologyRepository = Depends(get_cat_typ_repo),
):
    """List all category ↔ typology mappings."""
    return cat_typ_repo.list_all()


@router.put("/", response_model=CategoryTypologyOut)
def set_mapping(
    data: CategoryTypologySet,
    current_user: UserOut = Depends(get_current_user),
    cat_repo: CategoryRepository = Depends(get_category_repo),
    typ_repo: TypologyRepository = Depends(get_typology_repo),
    cat_typ_repo: CategoryTypologyRepository = Depends(get_cat_typ_repo),
):
    """Create or update a category ↔ typology mapping."""
    if not cat_repo.exists(data.category_id):
        raise HTTPException(status_code=404, detail="Category not found")
    if not typ_repo.exists(data.typology_id):
        raise HTTPException(status_code=404, detail="Typology not found")
    mapping = cat_typ_repo.set_mapping(
        category_id=data.category_id,
        typology_id=data.typology_id,
        enabled=data.enabled,
    )
    logger.info(
        "category_typology_set",
        category_id=data.category_id,
        typology_id=data.typology_id,
        enabled=data.enabled,
    )
    return mapping
