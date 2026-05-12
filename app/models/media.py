import uuid
import enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, ForeignKey, Enum as SAEnum, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.models.mixins import BaseMixin

if TYPE_CHECKING:
    from app.models.post import Post


class MediaType(str, enum.Enum):
    image = "image"
    video = "video"


class PostMedia(Base, BaseMixin):
    __tablename__ = "post_media"

    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True
    )

    media_type: Mapped[MediaType] = mapped_column(SAEnum(MediaType), nullable=False)

    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    storage_key: Mapped[str] = mapped_column(String(1000), nullable=False)

    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    post: Mapped["Post"] = relationship("Post", back_populates="media")

    def __repr__(self) -> str:
        return f"<PostMedia id={self.id} type={self.media_type}>"