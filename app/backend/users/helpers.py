import random
from backend.users.schemas import UserCreate
from backend.users.models import ProfilePicture, User
from app_factory import db


def create_user_instance(user_schema: UserCreate, commit=True): 
    user_data: dict = user_schema.model_dump(exclude=["password_confirm"])

    pfp_ids = [pfp.id for pfp in ProfilePicture.query.all()]
    user_data['profile_picture_id'] = random.choice(pfp_ids)

    new_user = User(**user_data)
    
    if commit:
        db.session.add(new_user)
        db.session.commit()
        
    return new_user
