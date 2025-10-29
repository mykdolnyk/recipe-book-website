from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator
from backend.recipes.models import PeriodType, Recipe, RecipeTag
from backend.utils.misc import generate_unique_slug, slugify
from backend.users.schemas import UserSchema


class PeriodTypeCreate(BaseModel):
    name: str

    @computed_field
    @property
    def slug(self) -> str:
        return slugify(self.name)
    
    @model_validator(mode='after')
    def check_slug_uniqueness(self):
        if PeriodType.query.filter_by(slug=self.slug).first():
            raise ValueError('A non-unique slug is generated for this object. ' 
                             + 'Consider choosing a unique name.')
        else:
            return self


class PeriodTypeSchema(BaseModel):
    id: int
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class RecipeTagCreate(BaseModel):
    name: str

    @computed_field
    @property
    def slug(self) -> str:
        return slugify(self.name)

    @model_validator(mode='after')
    def check_slug_uniqueness(self):
        if RecipeTag.query.filter_by(slug=self.slug).first():
            raise ValueError('A non-unique slug is generated for this object. ' 
                             + 'Consider choosing a unique name.')
        else:
            return self

class RecipeTagUpdate(RecipeTagCreate):
    ...

class RecipeTagSchema(BaseModel):
    id: int
    name: str
    slug: str
    
    model_config = ConfigDict(from_attributes=True)


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


class RecipeUpdate(BaseModel):
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
