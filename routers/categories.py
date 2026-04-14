"""CRUD endpoints for card categories."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from models.user import UserOut
from models.category import CategoryCreate, CategoryUpdate, CategoryOut
from repositories.protocols import CategoryRepository
from repositories.sqlalchemy import get_category_repo

logger = structlog.get_logger()

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=list[CategoryOut])
def list_categories(
    current_user: UserOut = Depends(get_current_user),
    cat_repo: CategoryRepository = Depends(get_category_repo),
):
    """List all categories."""
    return cat_repo.list_all()


@router.post("/", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    data: CategoryCreate,
    current_user: UserOut = Depends(get_current_user),
    cat_repo: CategoryRepository = Depends(get_category_repo),
):
    """Create a new category."""
    if cat_repo.name_exists(data.name):
        raise HTTPException(status_code=400, detail="Category name already exists")
    category = cat_repo.create(name=data.name, description=data.description)
    logger.info("category_created", category_id=category.id, name=category.name)
    return category


@router.patch("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    current_user: UserOut = Depends(get_current_user),
    cat_repo: CategoryRepository = Depends(get_category_repo),
):
    """Update a category."""
    category = cat_repo.update(category_id, data.model_dump(exclude_unset=True))
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    logger.info("category_updated", category_id=category_id)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    current_user: UserOut = Depends(get_current_user),
    cat_repo: CategoryRepository = Depends(get_category_repo),
):
    """Delete a category."""
    if not cat_repo.delete(category_id):
        raise HTTPException(status_code=404, detail="Category not found")
    logger.info("category_deleted", category_id=category_id)
