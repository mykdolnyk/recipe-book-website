from datetime import datetime
import enum
from typing import List, TYPE_CHECKING
from app_factory import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Column, ForeignKey, Integer, Table
if TYPE_CHECKING:
    from app.backend.users.models import User   


recipe_tag_association = Table(
    'recipe_recipe_tag_association',
    db.metadata,
    Column('tag_id', Integer, ForeignKey('recipe_tag.id')),
    Column('recipe_id', Integer, ForeignKey('recipe.id'))
)

recipe_mix_association = Table(
    'recipe_recipe_mix_association',
    db.metadata,
    Column('mix_id', Integer, ForeignKey('recipe_mix.id')),
    Column('recipe_id', Integer, ForeignKey('recipe.id'))
)

class PeriodType(db.Model):
    """Model representing a type of the meal depending on the time period (e.g., breakfast, lunch, dinner)."""
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    slug: Mapped[str] = mapped_column(unique=True, name='slug')
    recipes: Mapped[List['Recipe']] = relationship(back_populates='period_type')


class RecipeTag(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    slug: Mapped[str] = mapped_column(unique=True, name='slug')
    recipes: Mapped[List['Recipe']] = relationship(secondary=recipe_tag_association, back_populates='tags')


class Recipe(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    slug: Mapped[str] = mapped_column(unique=True, name='slug')
    author_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    author: Mapped["User"] = relationship(back_populates='recipes')
    calories: Mapped[int] = mapped_column()
    cooking_time: Mapped[int] = mapped_column()
    
    period_type_id: Mapped[int] = mapped_column(ForeignKey('period_type.id'))
    period_type: Mapped[PeriodType] = relationship(back_populates='recipes')
    
    ingredients: Mapped[str] = mapped_column()
    text: Mapped[str] = mapped_column()
    """The text of the recipe."""
    is_published: Mapped[bool] = mapped_column(default=False)
    is_visible: Mapped[bool] = mapped_column(default=True, server_default='1')
    
    created_on: Mapped[datetime] = mapped_column(default=datetime.now)
    published_on: Mapped[datetime] = mapped_column(nullable=True)
    last_updated: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)
    
    tags: Mapped[List[RecipeTag]] = relationship(secondary=recipe_tag_association, back_populates='recipes')
    mixes: Mapped[List['RecipeMix']] = relationship(secondary=recipe_mix_association, back_populates='recipes')
    applications: Mapped[List['RecipePublicationApplication']] = relationship(back_populates='recipe')
    likes: Mapped[List['Like']] = relationship(back_populates='recipe')
    
    @classmethod
    def visible(cls):
        return db.session.query(cls).filter_by(is_visible=True)
    
    def __repr__(self):
        return f"<Recipe: id={self.id}, author_id={self.author_id}>"
    

class RecipeMix(db.Model):
    """A model representing a mix of several recipes."""
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    author_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    author: Mapped["User"] = relationship(back_populates='mixes')
    created_on: Mapped[datetime] = mapped_column(default=datetime.now)
    recipes: Mapped[List[Recipe]] = relationship(secondary=recipe_mix_association, back_populates='mixes')


class RecipePublicationApplication(db.Model):
    """A model representing an application to publish the recipe."""
    class STATUSES(enum.IntEnum):
        NOT_REVIEWED = 0
        ACCEPTED = 1
        DECLINED = 2
    
    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey('recipe.id'))
    recipe: Mapped[Recipe] = relationship(back_populates='applications')
    comment: Mapped[str] = mapped_column()
    created_on: Mapped[datetime] = mapped_column(default=datetime.now)
    status: Mapped[int] = mapped_column(default=STATUSES.NOT_REVIEWED)
    last_reviewed_by: Mapped["User"] = relationship(back_populates='reviewed_applications')
    last_reviewed_by_id: Mapped[int] = mapped_column(ForeignKey('user.id'))


class Like(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    user: Mapped["User"] = relationship(back_populates='liked')
    recipe_id: Mapped[int] = mapped_column(ForeignKey('recipe.id'))
    recipe: Mapped[Recipe] = relationship(back_populates='likes')
    created_on: Mapped[datetime] = mapped_column(default=datetime.now)
