import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, SmallInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.models.mixins import BaseMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.post import Post
    from app.models.comment import Comment


class PostVote(Base, BaseMixin):
    __tablename__ = "post_votes"
    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="uq_post_votes_user_id_post_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    value: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # +1 or -1

    user: Mapped["User"] = relationship("User", back_populates="post_votes")
    post: Mapped["Post"] = relationship("Post", back_populates="votes")

    def __repr__(self) -> str:
        return f"<PostVote user={self.user_id} post={self.post_id} value={self.value}>"


class CommentVote(Base, BaseMixin):
    __tablename__ = "comment_votes"
    __table_args__ = (
        UniqueConstraint("user_id", "comment_id", name="uq_comment_votes_user_id_comment_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    comment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("comments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    value: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # +1 or -1

    user: Mapped["User"] = relationship("User", back_populates="comment_votes")
    comment: Mapped["Comment"] = relationship("Comment", back_populates="votes")

    def __repr__(self) -> str:
        return f"<CommentVote user={self.user_id} comment={self.comment_id} value={self.value}>"