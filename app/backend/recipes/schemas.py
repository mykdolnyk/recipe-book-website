from typing import Optional
from pydantic import BaseModel, Field, computed_field
from backend.recipes.models import Recipe
from backend.utils.misc import generate_unique_slug, slugify
from backend.users.schemas import UserSchema


class PeriodTypeCreate(BaseModel):
    name: str

    @computed_field
    @property
    def slug(self) -> str:
        return slugify(self.name)


class PeriodTypeSchema(BaseModel):
    id: int
    name: str
    slug: str


class RecipeTagCreate(BaseModel):
    name: str

    @computed_field
    @property
    def slug(self) -> str:
        return slugify(self.name)


class RecipeTagSchema(BaseModel):
    id: int
    name: str
    slug: str


class RecipeCreate(BaseModel):
    name: str = Field(..., max_length=64)
    calories: int
    cooking_time: int
    ingredients: str = Field(..., max_length=512)
    text: str = Field(..., max_length=8192)

    period_type_id: int
    author_id: int
    tags: Optional[list[int]] = Field(default_factory=list)
    
    @computed_field
    @property
    def slug(self) -> str:
        return generate_unique_slug(self.name, Recipe)


class RecipeEdit(BaseModel):
    name: Optional[str] = Field(default=None, max_length=64)
    calories: Optional[int] = None
    cooking_time: Optional[int] = None
    ingredients: Optional[str] = Field(default=None, max_length=512)
    text: Optional[str] = Field(default=None, max_length=8192)

    period_type_id: Optional[int] = None
    tags: Optional[list[int]] = Field(default_factory=list)


class RecipeSchema(BaseModel):
    id: int
    name: str
    calories: int
    cooking_time: int
    ingredients: str
    text: str

    period_type: PeriodTypeSchema | None
    author: UserSchema | None
    tags: list[RecipeTagSchema]
    slug: str
    
    class Config:
        from_attributes = True
