from backend.users.schemas import UserCreate
from backend.users.models import User
from app_factory import db


def create_user_instance(user_schema: UserCreate, commit=True): 
    user_data: dict = user_schema.model_dump(exclude=["password_confirm"])
    
    new_user = User(**user_data)
    
    if commit:
        db.session.add(new_user)
        db.session.commit()
        
    return new_user
