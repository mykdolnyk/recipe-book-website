from datetime import datetime
from typing import TYPE_CHECKING, List
from app_factory import db, login_manager
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_login import UserMixin
if TYPE_CHECKING:
    from app.backend.recipes.models import Like, Recipe, RecipeMix, RecipePublicationApplication


class User(db.Model, UserMixin):
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str] = mapped_column()
    
    name: Mapped[str] = mapped_column()
    bio: Mapped[str] = mapped_column()

    recipes: Mapped[List['Recipe']] = relationship(back_populates='author')
    mixes: Mapped[List['RecipeMix']] = relationship(back_populates='author')
    liked: Mapped[List['Like']] = relationship(back_populates='user')
    
    reviewed_applications: Mapped[List['RecipePublicationApplication']] = relationship(back_populates='last_reviewed_by')
    
    created_on: Mapped[datetime] = mapped_column(default=datetime.now)
    
    def info_dict(self):
        dictionary = {
            "id": self.id,
            "name": self.name,
            "bio": self.bio,
        }
        
        return dictionary
