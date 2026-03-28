from sqlalchemy import  Column, Integer, String, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(16))
    email: Mapped[str] = mapped_column(String(254))
    password: Mapped[str] = mapped_column(String(32))
    subscribe: Mapped[List["User.id"]] = mapped_column(int)
    posts: Mapped[List["Post"]] = relationship(
        "Post", 
        back_populates="author", 
        cascade="all, delete-orphan"
        )

class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(64))
    text: Mapped[str] = mapped_column(String(300))