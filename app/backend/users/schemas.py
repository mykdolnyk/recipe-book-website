from typing import Optional, Self
from pydantic import BaseModel, ConfigDict, Field, EmailStr, computed_field, field_validator, model_validator
from backend.utils.errors import PasswordRequirements
from backend.users.models import ProfilePicture, User
from app_factory import password_policy
import bcrypt

import config


def check_email_availability(email: EmailStr):
    if email is None:
        return None

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
            msgs = [
                PasswordRequirements[e.name().upper()].value for e in errors
            ]  
            raise ValueError(
                "Password does not meet strength requirements:\n" + ";\n".join(msgs))
        return password

    @field_validator('password', mode='after')
    def hash_password(password: str):
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password=password.encode(),
                                        salt=salt).decode()
        return hashed_password

    _validate_email = field_validator('email')(check_email_availability)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=64)
    bio: str | None = Field(default=None, max_length=512)
    email: EmailStr | None = None
    profile_picture_id: int | None = None

    _validate_email = field_validator('email')(check_email_availability)
    
    @field_validator('profile_picture_id')
    def validate_profile_picture_id(profile_picture_id: int):
        if not ProfilePicture.query.filter_by(id=profile_picture_id).first():
            raise ValueError(
                'Profile Picture with such ID doesn\'t exist.')
        return profile_picture_id


class UserSchema(BaseModel):
    id: int
    name: str
    profile_picture: Optional['ProfilePictureSchema'] = None

    model_config = ConfigDict(from_attributes=True)


class UserDetailedSchema(UserSchema):
    bio: str
    recipe_count: int
    like_count: int


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., max_length=128)

    @computed_field
    @property
    def user(self) -> User:
        user = User.active().filter_by(email=self.email).first()
        return user

    @model_validator(mode='after')
    def check_credentials(self):
        if not self.user:
            raise ValueError("Login credentials are incorrect.")

        try:
            credentials_match = bcrypt.checkpw(
                self.password.encode(), self.user.password.encode())
        except Exception as exc:
            print(exc)
            raise exc

        if not credentials_match:
            raise ValueError("Login credentials are incorrect.")

        return self

    model_config = ConfigDict(from_attributes=True,
                              arbitrary_types_allowed=True)


class ProfilePictureSchema(BaseModel):
    id: int
    file_path: str = Field(exclude=True)
    
    @computed_field
    @property
    def path(self) -> str:
        return (config.STATIC_URL_PATH / self.file_path).as_posix()
    
    model_config = ConfigDict(from_attributes=True)