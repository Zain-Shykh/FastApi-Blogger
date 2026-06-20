from __future__ import annotations
from datetime import UTC, datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base
from config import settings

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    image_file: Mapped[str|None] = mapped_column(String(200), nullable=True, default=None)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    posts: Mapped[list[Post]] = relationship(back_populates="author", cascade="all, delete-orphan")
    reset_tokens: Mapped[list[PasswordResetToken]] = relationship(back_populates="user", cascade="all, delete-orphan")

    @property
    def image_path(self)->str:
        if self.image_file:
            return f"{settings.s3_endpoint_url}/storage/v1/object/public/{settings.s3_bucket_name}/{self.image_file}"
        return "/static/profile_pics/default.jpg"


class Post(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    date_posted: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    likes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    author: Mapped[User] = relationship(back_populates="posts")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    user: Mapped[User] = relationship(back_populates="reset_tokens")