import uuid
import enum
from typing import TYPE_CHECKING, List, Optional, Any

from sqlalchemy import String, Text, Boolean, ForeignKey, Enum as SAEnum, Integer, Computed
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR

from app.database import Base
from app.models.mixins import BaseMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.community import Community
    from app.models.comment import Comment
    from app.models.vote import PostVote
    from app.models.media import PostMedia


class PostStatus(str, enum.Enum):
    active  = "active"
    removed = "removed"
    deleted = "deleted"


class Post(Base, BaseMixin):
    __tablename__ = "posts"

    # ── Content ────────────────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Anonymous ──────────────────────────────────────────────────────────────
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Status ────────────────────────────────────────────────────────────────
    status: Mapped[PostStatus] = mapped_column(
        SAEnum(PostStatus), default=PostStatus.active, nullable=False, index=True
    )
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Counters (denormalised) ────────────────────────────────────────────────
    vote_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    upvote_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    downvote_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    flair: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # ── Full-text search vector ────────────────────────────────────────────────
    search_vector: Mapped[Any] = mapped_column(
        TSVECTOR,
        Computed(
            "setweight(to_tsvector('english', coalesce(title, '')), 'A') || "
            "setweight(to_tsvector('english', coalesce(body, '')), 'B')",
            persisted=True,
        ),
        nullable=True,
    )

    # ── Foreign keys ──────────────────────────────────────────────────────────
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    community_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("communities.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    author: Mapped["User"] = relationship("User", back_populates="posts")
    community: Mapped[Optional["Community"]] = relationship("Community", back_populates="posts")
    comments: Mapped[List["Comment"]] = relationship(
        "Comment", back_populates="post", cascade="all, delete-orphan"
    )
    votes: Mapped[List["PostVote"]] = relationship(
        "PostVote", back_populates="post", cascade="all, delete-orphan"
    )
    media: Mapped[List["PostMedia"]] = relationship(
        "PostMedia", back_populates="post", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Post id={self.id} title={self.title[:30]!r}>"