import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import BaseMixin

if TYPE_CHECKING:
    from app.models.post import Post
    from app.models.comment import Comment
    from app.models.vote import PostVote, CommentVote
    from app.models.community import Community, CommunityMember
    from app.models.notification import Notification


class User(Base, BaseMixin):
    __tablename__ = "users"

    # ── Identity ───────────────────────────────────────────────────────────────
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # ── Profile ────────────────────────────────────────────────────────────────
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # ── Flags ──────────────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Karma ──────────────────────────────────────────────────────────────────
    post_karma: Mapped[int] = mapped_column(default=0, nullable=False)
    comment_karma: Mapped[int] = mapped_column(default=0, nullable=False)

    # ── Relationships ──────────────────────────────────────────────────────────
    posts: Mapped[List["Post"]] = relationship(
        "Post", back_populates="author", cascade="all, delete-orphan"
    )
    comments: Mapped[List["Comment"]] = relationship(
        "Comment", back_populates="author", cascade="all, delete-orphan"
    )
    post_votes: Mapped[List["PostVote"]] = relationship(
        "PostVote", back_populates="user", cascade="all, delete-orphan"
    )
    comment_votes: Mapped[List["CommentVote"]] = relationship(
        "CommentVote", back_populates="user", cascade="all, delete-orphan"
    )
    communities_created: Mapped[List["Community"]] = relationship(
        "Community", back_populates="creator"
    )
    community_memberships: Mapped[List["CommunityMember"]] = relationship(
        "CommunityMember", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"