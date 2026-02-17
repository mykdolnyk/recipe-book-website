from datetime import datetime
from typing import Optional
import flask_login
from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator
from backend.recipes.models import MealType, Recipe, RecipeTag
from backend.utils.misc import generate_unique_slug, slugify
from backend.users.schemas import UserSchema


class MealTypeCreate(BaseModel):
    name: str

    @computed_field
    @property
    def slug(self) -> str:
        return slugify(self.name)

    @model_validator(mode='after')
    def check_slug_uniqueness(self):
        if MealType.query.filter_by(slug=self.slug).first():
            raise ValueError('A non-unique slug is generated for this object. '
                             + 'Consider choosing a unique name.')
        else:
            return self


class MealTypeSchema(BaseModel):
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
    description: str | None = Field(..., max_length=512)
    text: str = Field(..., max_length=8192)

    meal_type_id: int
    tags: Optional[list[int]] = Field(default_factory=list)

    @computed_field
    @property
    def slug(self) -> str:
        return generate_unique_slug(self.name, Recipe)

    @computed_field
    @property
    def author_id(self) -> int:
        return flask_login.current_user.id

    @field_validator('tags')
    def validate_tags(tags: list[int]):
        for tag in tags:
            if not RecipeTag.query.filter(RecipeTag.id == tag).first():
                raise ValueError(
                    f"Recipe Tag with such ID doesn't exist: {tag}.")
        return tags

    @field_validator('meal_type_id')
    def validate_meal_type(meal_type_id: int):
        if not MealType.query.filter(MealType.id == meal_type_id).first():
            raise ValueError(
                f"Meal Type with such ID doesn't exist: {meal_type_id}.")
        return meal_type_id


class RecipeUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=64)
    calories: Optional[int] = None
    cooking_time: Optional[int] = None
    ingredients: Optional[str] = Field(default=None, max_length=512)
    description: Optional[str] = Field(default=None, max_length=512)
    text: Optional[str] = Field(default=None, max_length=8192)

    meal_type_id: Optional[int] = None
    tags: Optional[list[int]] = Field(default_factory=list)


class RecipeUpdateStatus(BaseModel):
    is_visible: Optional[bool] = None
    is_published: Optional[bool] = None


class RecipeSchema(BaseModel):
    id: int
    name: str
    calories: int
    cooking_time: int
    ingredients: str
    description: str | None
    text: str

    meal_type: MealTypeSchema | None
    author: UserSchema | None
    tags: list[RecipeTagSchema]
    slug: str
    is_published: bool
    
    like_count: int

    model_config = ConfigDict(from_attributes=True)


class RecipeDetailedSchema(RecipeSchema):
    is_published: bool
    is_visible: bool


class RecipePublicationApplicationCreate(BaseModel):
    comment: str | None = None


class RecipePublicationApplicationSchema(BaseModel):
    id: int
    recipe_id: int
    comment: str | None
    created_on: datetime
    status: int
    last_reviewed_by_id: int | None

    model_config = ConfigDict(from_attributes=True)


class RecipePublicationApplicationUpdate(BaseModel):
    status: Optional[int]


class RecipeMixCreate(BaseModel):
    include_tags: list[int] = None
    exclude_tags: list[int] = None
    max_calories: int | None = None
    min_calories: int | None = None
    meal_type_ids: list[int]
    personal_only: bool = False
    public_only: bool = False


class RecipeMixSchema(BaseModel):
    id: int
    name: str
    author: UserSchema | None
    created_on: datetime
    recipes: list[RecipeSchema]

    model_config = ConfigDict(from_attributes=True)


class RecipeMixUpdate(BaseModel):
    name: str
