from uuid import UUID
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    display_name: Optional[str] = Field(None, max_length=100)


class UserUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None


class UserOut(BaseModel):
    id: UUID
    username: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    post_karma: int
    comment_karma: int
    created_at: datetime

    model_config = {"from_attributes": True}


class UserPrivateOut(UserOut):
    """Returned only to the user themselves — includes email."""
    email: str