"""CategoryTypology domain models."""

from pydantic import BaseModel

from models.category import CategoryOut
from models.typology import TypologyOut


class CategoryTypologySet(BaseModel):
    category_id: int
    typology_id: int
    enabled: bool


class CategoryTypologyOut(BaseModel):
    category_id: int
    typology_id: int
    enabled: bool
    category: CategoryOut
    typology: TypologyOut
    model_config = {"from_attributes": True}
