from pydantic import *


class Post(BaseModel):
    id: int
    author_id: int
    title: str
    text: str
    rating_up: list[int]
    rating_down: list[int]


class PostCreate(BaseModel):
    author_id: int
    title: str
    text: str
    rating_up: list[int]
    rating_down: list[int]