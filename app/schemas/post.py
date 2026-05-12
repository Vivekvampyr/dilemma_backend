from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.post import PostStatus
from app.schemas.user import UserOut
from app.schemas.media import MediaOut


class PostCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=300)
    body: Optional[str] = Field(None, max_length=10000)
    is_anonymous: bool = False
    community_id: Optional[UUID] = None
    flair: Optional[str] = Field(None, max_length=50)


class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=300)
    body: Optional[str] = Field(None, max_length=10000)
    flair: Optional[str] = Field(None, max_length=50)


class PostOut(BaseModel):
    id: UUID
    title: str
    body: Optional[str]
    is_anonymous: bool
    status: PostStatus
    is_locked: bool
    is_pinned: bool
    vote_score: int
    upvote_count: int
    downvote_count: int
    comment_count: int
    view_count: int
    flair: Optional[str]
    community_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    # author is None when post is anonymous
    author: Optional[UserOut]
    media: List[MediaOut] = []

    # user's own vote on this post (-1, 0, +1) — populated at query time
    user_vote: Optional[int] = 0

    model_config = {"from_attributes": True}