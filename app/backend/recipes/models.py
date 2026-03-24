from datetime import datetime
import enum
from typing import List, TYPE_CHECKING, Optional
from sqlalchemy.orm import column_property
from flask_login import current_user
from app_factory import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Column, ForeignKey, Integer, Table, and_, func, or_, select
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


class MealType(db.Model):
    """Model representing a type of the meal depending on the time period (e.g., breakfast, lunch, dinner)."""
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    slug: Mapped[str] = mapped_column(unique=True, name='slug')
    recipes: Mapped[List['Recipe']] = relationship(back_populates='meal_type')
    
    def __repr__(self):
        return f"<MealType: name='{self.name}', id={self.id}>"


class RecipeTag(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    slug: Mapped[str] = mapped_column(unique=True, name='slug')
    recipes: Mapped[List['Recipe']] = relationship(
        secondary=recipe_tag_association, back_populates='tags')
    
    def __repr__(self):
        return f"<RecipeTag: name='{self.name}', id={self.id}>"


class Like(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    user: Mapped["User"] = relationship(back_populates='liked')
    recipe_id: Mapped[int] = mapped_column(ForeignKey('recipe.id'))
    recipe: Mapped["Recipe"] = relationship(back_populates='likes')
    created_on: Mapped[datetime] = mapped_column(default=datetime.now)

    __table_args__ = (
        db.UniqueConstraint('recipe_id', 'user_id',
                            name='uq_like_recipe_user'),
    )


class Recipe(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    slug: Mapped[str] = mapped_column(unique=True, name='slug')
    author_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    author: Mapped["User"] = relationship(back_populates='recipes')
    calories: Mapped[int] = mapped_column()
    cooking_time: Mapped[int] = mapped_column()

    meal_type_id: Mapped[int] = mapped_column(ForeignKey('meal_type.id'))
    meal_type: Mapped[MealType] = relationship(back_populates='recipes')

    ingredients: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column(nullable=True, default=None)
    text: Mapped[str] = mapped_column()
    """The text of the recipe."""
    is_published: Mapped[bool] = mapped_column(default=False)
    is_visible: Mapped[bool] = mapped_column(default=True, server_default='1')

    created_on: Mapped[datetime] = mapped_column(default=datetime.now)
    published_on: Mapped[datetime] = mapped_column(nullable=True)
    last_updated: Mapped[datetime] = mapped_column(
        default=datetime.now, onupdate=datetime.now)

    tags: Mapped[List[RecipeTag]] = relationship(
        secondary=recipe_tag_association, back_populates='recipes')
    mixes: Mapped[List['RecipeMix']] = relationship(
        secondary=recipe_mix_association, back_populates='recipes')
    applications: Mapped[List['RecipePublicationApplication']
                         ] = relationship(back_populates='recipe')
    likes: Mapped[List['Like']] = relationship(back_populates='recipe')

    like_count = column_property(
        select(func.count(Like.id))
        .where(Like.recipe_id == id)
        .correlate_except(Like)
        .scalar_subquery()
    )

    @classmethod
    def visible(cls):
        return db.session.query(cls).filter_by(is_visible=True)

    @classmethod
    def published(cls):
        return db.session.query(cls).filter_by(is_visible=True, is_published=True)

    @classmethod
    def ua_query(cls, user: 'User' = None, force_exclude_hidden=False, force_exclude_not_personal_unpublished=False):
        """User-aware query that filters out objects that the current user
        shouldn't see."""
        if user is None:
            user = current_user

        if user.is_superuser:
            query = db.session.query(cls)

        elif user.is_anonymous:
            query = db.session.query(cls).filter(
                and_(
                    cls.is_visible.is_(True),
                    cls.is_published.is_(True)
                ))
        else:
            # published recipes and personal ones
            query = db.session.query(cls).filter(
                or_(
                    and_(
                        cls.is_visible.is_(True),
                        cls.is_published.is_(True)
                    ),
                    and_(
                        cls.author_id == user.id,
                        cls.is_visible.is_(True),
                    )
                )
            )
        if force_exclude_hidden:
            query = query.filter(cls.is_visible == True)

        if force_exclude_not_personal_unpublished:
            query = query.filter(
                or_(
                    cls.is_published == True,
                    cls.author_id == user.id
                )
            )

        return query

    def __repr__(self):
        return f"<Recipe: name='{self.name}', id={self.id}, author_id={self.author_id}>"


class RecipeMix(db.Model):
    """A model representing a mix of several recipes."""
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    author_id: Mapped[int] = mapped_column(
        ForeignKey('user.id'), nullable=True)
    author: Mapped["User"] = relationship(back_populates='mixes')
    created_on: Mapped[datetime] = mapped_column(default=datetime.now)
    recipes: Mapped[List[Recipe]] = relationship(
        secondary=recipe_mix_association, back_populates='mixes')

    def __repr__(self):
        return f"<RecipeMix: id={self.id}, author_id={self.author_id}>"


class RecipePublicationApplication(db.Model):
    """A model representing an application to publish the recipe."""
    class STATUSES(enum.IntEnum):
        NOT_REVIEWED = 0
        ACCEPTED = 1
        DECLINED = 2

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey('recipe.id'))
    recipe: Mapped[Recipe] = relationship(back_populates='applications')
    comment: Mapped[Optional[str]] = mapped_column()
    created_on: Mapped[datetime] = mapped_column(default=datetime.now)
    status: Mapped[int] = mapped_column(default=STATUSES.NOT_REVIEWED)
    last_reviewed_by: Mapped["User"] = relationship(
        back_populates='reviewed_applications')
    last_reviewed_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey('user.id'))
    
    def __repr__(self):
        return f"<RecipeApplication: recipe.name='{self.recipe.name}', id={self.id}, author_id={self.recipe.author_id}>"
