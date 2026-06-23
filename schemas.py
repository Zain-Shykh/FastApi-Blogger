from pydantic import BaseModel, Field, ConfigDict, EmailStr
from datetime import datetime


class UserBase(BaseModel):
    username:str = Field(min_length=1, max_length=50)
    email:EmailStr = Field(max_length=120)

class UserCreate(UserBase):
    password:str = Field(min_length=8)

class UserPublic(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id:int
    username:str
    image_path:str
    image_file:str|None

class UserPrivate(UserPublic):
    email:EmailStr

class UserUpdate(BaseModel):
    username:str | None = Field(default=None, min_length=1, max_length=50)
    email:EmailStr | None = Field(default=None, max_length=120)

class Token(BaseModel):
    access_token:str
    token_type:str

class PostBase(BaseModel):
    title:str = Field(min_length=1, max_length=100)
    content:str = Field(min_length=10)

class PostCreate(PostBase):
    pass

class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)
    id:int
    user_id:int
    date_posted:datetime
    author:UserPublic

class PostUpdate(BaseModel):
    title:str | None = Field(default=None, min_length=1, max_length=100)
    content:str | None = Field(default=None, min_length=10)


class PaginatedPostsResponse(BaseModel):
    posts: list[PostResponse]
    total: int
    skip: int
    limit: int
    has_more: int


class ForgotPasswordRequest(BaseModel):
    email:EmailStr = Field(max_length=120)

class ResetPasswordRequest(BaseModel):
    token:str
    new_password:str = Field(min_length=8)

class ChangePasswordRequest(BaseModel):
    current_password:str
    new_password:str = Field(min_length=8)


class CommentCreate(BaseModel):
    content:str = Field(min_length=1, max_length=500)

class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:int
    content:str
    date_posted:datetime
    user:UserPublic
    post_id:int
    parent_id:int|None
    replies:list["CommentResponse"] = []