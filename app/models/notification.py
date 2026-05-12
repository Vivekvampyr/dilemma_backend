import uuid
import enum
from typing import Optional

from sqlalchemy import String, Boolean, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.models.mixins import BaseMixin


class NotificationType(str, enum.Enum):
    comment_on_post     = "comment_on_post"
    reply_on_comment    = "reply_on_comment"
    upvote_on_post      = "upvote_on_post"
    upvote_on_comment   = "upvote_on_comment"
    community_post      = "community_post"
    mod_removed_post    = "mod_removed_post"
    mod_removed_comment = "mod_removed_comment"
    banned              = "banned"


class Notification(Base, BaseMixin):
    __tablename__ = "notifications"

    recipient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    type: Mapped[NotificationType] = mapped_column(
        SAEnum(NotificationType), nullable=False, index=True
    )

    message: Mapped[str] = mapped_column(Text, nullable=False)

    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    recipient = relationship("User", foreign_keys=[recipient_id])
    actor     = relationship("User", foreign_keys=[actor_id])

    def __repr__(self) -> str:
        return f"<Notification type={self.type} recipient={self.recipient_id}>"