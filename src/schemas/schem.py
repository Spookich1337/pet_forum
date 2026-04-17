from pydantic import *
from typing import Optional


class UserLogin(BaseModel):
    email: str
    password: str


class UserSub(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class UserShortResponse(BaseModel):
    id: int
    name: str
    subscriptions: list[UserSub]
    subscribers: list[UserSub]

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    subscriptions: list[UserSub]
    subscribers: list[UserSub]

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


class UserList(BaseModel):
    count : int
    users : list[UserShortResponse]


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
    title: str
    text: str


class PostUpdate(BaseModel):
    title: Optional[str] = None
    text: Optional[str] = None