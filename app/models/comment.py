import uuid
import enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Text, Boolean, ForeignKey, Enum as SAEnum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.models.mixins import BaseMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.post import Post
    from app.models.vote import CommentVote


class CommentStatus(str, enum.Enum):
    active  = "active"
    removed = "removed"
    deleted = "deleted"


class Comment(Base, BaseMixin):
    __tablename__ = "comments"

    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    status: Mapped[CommentStatus] = mapped_column(
        SAEnum(CommentStatus), default=CommentStatus.active, nullable=False
    )

    # ── Counters ───────────────────────────────────────────────────────────────
    vote_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    upvote_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    downvote_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ── Foreign keys ──────────────────────────────────────────────────────────
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    author: Mapped["User"] = relationship("User", back_populates="comments")
    post: Mapped["Post"] = relationship("Post", back_populates="comments")
    parent: Mapped[Optional["Comment"]] = relationship(
        "Comment", back_populates="replies", remote_side="Comment.id"
    )
    replies: Mapped[List["Comment"]] = relationship(
        "Comment", back_populates="parent", cascade="all, delete-orphan"
    )
    votes: Mapped[List["CommentVote"]] = relationship(
        "CommentVote", back_populates="comment", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Comment id={self.id} post={self.post_id}>"