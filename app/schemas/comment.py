from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from app.schemas.user import UserOut


class CommentCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=5000)
    is_anonymous: bool = False
    parent_id: Optional[UUID] = None   # None = top-level comment


class CommentUpdate(BaseModel):
    body: str = Field(..., min_length=1, max_length=5000)


class CommentOut(BaseModel):
    id: UUID
    body: str
    is_anonymous: bool
    vote_score: int
    upvote_count: int
    downvote_count: int
    post_id: UUID
    parent_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    author: Optional[UserOut]           # None when anonymous
    replies: List["CommentOut"] = []    # nested replies (one level)
    user_vote: Optional[int] = 0

    model_config = {"from_attributes": True}


CommentOut.model_rebuild()              # required for self-referential model