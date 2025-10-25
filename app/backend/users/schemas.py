from typing import Self
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
from backend.users.models import User
from app_factory import password_policy
import bcrypt


def check_email_availability(email: EmailStr):
    if User.query.filter(User.email == email).first():
        raise ValueError('The email is already taken.')
    return email


class UserCreate(BaseModel):
    name: str = Field(..., max_length=64)
    email: EmailStr 
    password: str = Field(..., min_length=8, max_length=128)
    password_confirm: str

    @model_validator(mode='before')
    def match_passwords(self) -> Self:
        if self.get('password') != self.get('password_confirm'):
            raise ValueError("Passwords do not match.")
        return self

    @field_validator('password')
    def check_password_strength(password: str):
        errors = password_policy.test(password)
        if errors:
            msgs = [str(e) for e in errors]
            raise ValueError(
                "Password does not meet strength requirements: " + "; ".join(msgs))
        return password

    @field_validator('password', mode='after')
    def hash_password(password: str):
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password=password.encode(),
                                        salt=salt).decode()
        return hashed_password

    _validate_email = field_validator('email')(check_email_availability)
    

class UserEdit(BaseModel):
    name: str = Field(..., max_length=64)
    bio: str = Field(..., max_length=512)
    email: EmailStr

    _validate_email = field_validator('email')(check_email_availability)


class UserSchema(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True
