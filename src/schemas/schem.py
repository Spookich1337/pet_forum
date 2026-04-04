from pydantic import *
from typing import Optional


class UserShortResponse(BaseModel):
    id: int
    name: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    password: str
    subscriptions: list[UserShortResponse]
    subscribers: list[UserShortResponse]


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


class PostResponse(BaseModel):
    id: int
    author_id: int
    title: str
    text: str
    rating_up: list[int]
    rating_down: list[int]


class PostList(BaseModel):
    count : int
    posts : list[PostResponse]


class PostCreate(BaseModel):
    author_id: int
    title: str
    text: str


class PostUpdate(BaseModel):
    author_id: Optional[int]= None
    title: Optional[str] = None
    text: Optional[str] = None
    rating_up: Optional[list[int]] = None
    rating_down: Optional[list[int]] = None