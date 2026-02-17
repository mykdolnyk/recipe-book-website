from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, func, literal_column, select, text
from app_factory import db
from sqlalchemy.orm import Mapped, mapped_column, relationship, column_property
from flask_login import UserMixin
if TYPE_CHECKING:
    from app.backend.recipes.models import Like, Recipe, RecipeMix, RecipePublicationApplication


class User(db.Model, UserMixin):
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str] = mapped_column()
    
    name: Mapped[str] = mapped_column()
    bio: Mapped[str] = mapped_column(default='')
    profile_picture_id: Mapped[int] = mapped_column(ForeignKey('profile_picture.id'))
    profile_picture: Mapped['ProfilePicture'] = relationship(back_populates='users')

    recipes: Mapped[List['Recipe']] = relationship(back_populates='author')
    mixes: Mapped[List['RecipeMix']] = relationship(back_populates='author')
    liked: Mapped[List['Like']] = relationship(back_populates='user')
    
    reviewed_applications: Mapped[List['RecipePublicationApplication']] = relationship(back_populates='last_reviewed_by')
    
    created_on: Mapped[datetime] = mapped_column(default=datetime.now)
    
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False, server_default='0')
    
    like_count = column_property(
        select(func.count(literal_column("like.id")))
        .select_from(text("like, recipe"))
        .where(literal_column("recipe.author_id = user.id AND like.recipe_id = recipe.id"))
        .scalar_subquery()
    )
    
    recipe_count = column_property(
        select(func.count(literal_column("recipe.id")))
        .select_from(text("recipe"))
        .where(literal_column("recipe.author_id") == id)
        .scalar_subquery()
    )

    
    @classmethod
    def active(cls):
        return db.session.query(cls).filter_by(is_active=True)

    def __repr__(self):
        return f"<User: id={self.id}, name='{self.name}'>"
    

class ProfilePicture(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    file_path: Mapped[str] = mapped_column()
    users: Mapped[List[User]] = relationship(back_populates='profile_picture')
    