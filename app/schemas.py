from typing import Optional, List
from pydantic import BaseModel, constr
from datetime import datetime


class UserCreate(BaseModel):
    username: constr(min_length=3, max_length=32)
    password: constr(min_length=6)
    display_name: Optional[str]


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PostCreate(BaseModel):
    content: constr(min_length=1, max_length=280)
    parent_id: Optional[int] = None


class PostOut(BaseModel):
    id: int
    author_username: str
    author_id: int
    content: str
    created_at: datetime
    parent_id: Optional[int]
    likes: int
    replies: List["PostOut"] = []

    class Config:
        orm_mode = True


class ProfileOut(BaseModel):
    id: int
    username: str
    display_name: Optional[str]
    created_at: datetime
    posts: List[PostOut] = []

    class Config:
        orm_mode = True
