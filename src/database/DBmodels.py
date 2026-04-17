from sqlalchemy import Integer, String, ForeignKey, Table, Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ARRAY
from typing import List


Base = declarative_base()


user_subscriptions = Table(
    "user_subscriptions",
    Base.metadata,
    Column('subscriber_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('subscribed_to_id', Integer, ForeignKey('users.id'), primary_key=True)
)


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(32), unique=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password: Mapped[str] = mapped_column(String(72))
    subscriptions: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_subscriptions,
        primaryjoin=id == user_subscriptions.c.subscriber_id,
        secondaryjoin=id == user_subscriptions.c.subscribed_to_id,
        back_populates="subscribers"
    )
    subscribers: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_subscriptions,
        primaryjoin=id == user_subscriptions.c.subscribed_to_id,
        secondaryjoin=id == user_subscriptions.c.subscriber_id,
        back_populates="subscriptions"
    )
    posts: Mapped[List["Post"]] = relationship(
        "Post", 
        back_populates="author", 
        cascade="all, delete-orphan"
    )


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    title: Mapped[str] = mapped_column(String(64), unique=True)
    text: Mapped[str] = mapped_column(String(300), nullable=True)
    rating_up: Mapped[list[int]] = mapped_column(ARRAY(Integer, dimensions=1), default=list)
    rating_down: Mapped[list[int]] = mapped_column(ARRAY(Integer, dimensions=1), default=list)
    author: Mapped["User"] = relationship(
        "User", 
        back_populates="posts"
    )