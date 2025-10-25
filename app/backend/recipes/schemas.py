from pydantic import BaseModel, computed_field
from slugify import slugify

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
    name: str
    calories: int
    cooking_time: int
    ingredients: str
    text: str

    period_type_id: int
    author_id: int
    tags: list[int] = list()
    
    @computed_field
    @property
    def slug(self) -> str:
        return slugify(self.name)


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
    
    class Config:
        from_attributes = True
