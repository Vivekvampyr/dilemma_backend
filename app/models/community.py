import uuid
import enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, Text, Boolean, ForeignKey, Enum as SAEnum, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.models.mixins import BaseMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.post import Post


class CommunityVisibility(str, enum.Enum):
    public     = "public"
    private    = "private"
    restricted = "restricted"


class CommunityRole(str, enum.Enum):
    member    = "member"
    moderator = "moderator"
    admin     = "admin"


class Community(Base, BaseMixin):
    __tablename__ = "communities"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    banner_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    visibility: Mapped[CommunityVisibility] = mapped_column(
        SAEnum(CommunityVisibility), default=CommunityVisibility.public, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    member_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    creator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    creator: Mapped[Optional["User"]] = relationship("User", back_populates="communities_created")
    members: Mapped[List["CommunityMember"]] = relationship(
        "CommunityMember", back_populates="community", cascade="all, delete-orphan"
    )
    posts: Mapped[List["Post"]] = relationship("Post", back_populates="community")

    def __repr__(self) -> str:
        return f"<Community name={self.name!r}>"


class CommunityMember(Base, BaseMixin):
    __tablename__ = "community_members"
    __table_args__ = (
        UniqueConstraint("community_id", "user_id", name="uq_community_members_community_id_user_id"),
    )

    community_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("communities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[CommunityRole] = mapped_column(
        SAEnum(CommunityRole), default=CommunityRole.member, nullable=False
    )

    community: Mapped["Community"] = relationship("Community", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="community_memberships")