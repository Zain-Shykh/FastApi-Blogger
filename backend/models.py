from __future__ import annotations
from datetime import UTC, datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base
from config import settings


def _public_object_url(prefix:str, filename:str) -> str:
    # settings.s3_endpoint_url is the S3-protocol endpoint (".../storage/v1/s3"), used by boto3.
    # The public HTTP URL for an object lives at ".../storage/v1/object/public/<bucket>/<key>" —
    # note no "/s3" segment — so it must be stripped before building the public URL.
    base = (settings.s3_endpoint_url or "").removesuffix("/s3")
    return f"{base}/object/public/{settings.s3_bucket_name}/{prefix}/{filename}"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    image_file: Mapped[str|None] = mapped_column(String(200), nullable=True, default=None)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    is_admin: Mapped[bool] = mapped_column(nullable=False, default=False)


    posts: Mapped[list[Post]] = relationship(back_populates="author", cascade="all, delete-orphan")
    reset_tokens: Mapped[list[PasswordResetToken]] = relationship(back_populates="user", cascade="all, delete-orphan")
    likes: Mapped[list[Like]] = relationship(back_populates="user", cascade="all, delete-orphan")
    comments: Mapped[list[Comment]] = relationship(back_populates="user", cascade="all, delete-orphan")

    @property
    def image_path(self)->str:
        if self.image_file:
            return _public_object_url("profile_images", self.image_file)
        return "/media/profile_pics/default.jpg"


class Post(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    date_posted: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    image_file: Mapped[str|None] = mapped_column(String(200), nullable=True, default=None)

    author: Mapped[User] = relationship(back_populates="posts")
    likes: Mapped[list[Like]] = relationship(back_populates="post", cascade="all, delete-orphan")
    comments: Mapped[list[Comment]] = relationship(back_populates="post", cascade="all, delete-orphan")

    @property
    def image_path(self)->str:
        if self.image_file:
            return _public_object_url("post", self.image_file)
        return "/media/thumbnails/default.jpg"

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


    user: Mapped[User] = relationship(back_populates="reset_tokens")



class Like(Base):
    __tablename__ = "likes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id",  ondelete="CASCADE"), nullable=False)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)

    user: Mapped[User] = relationship(back_populates="likes")
    post: Mapped[Post] = relationship(back_populates="likes")



class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    date_posted: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    parent_id: Mapped[int|None] = mapped_column(Integer, ForeignKey("comments.id"), nullable=True, index=True)

    user: Mapped[User] = relationship(back_populates="comments")
    post: Mapped[Post] = relationship(back_populates="comments")
    replies: Mapped[list[Comment]] = relationship("Comment", back_populates="parent", cascade="all, delete-orphan")
    parent: Mapped[Comment|None] = relationship("Comment", back_populates="replies", remote_side=[id])