from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.community import CommunityVisibility, CommunityRole


class CommunityCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    display_name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    visibility: CommunityVisibility = CommunityVisibility.public


class CommunityUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    icon_url: Optional[str] = None
    banner_url: Optional[str] = None
    visibility: Optional[CommunityVisibility] = None


class CommunityOut(BaseModel):
    id: UUID
    name: str
    display_name: str
    description: Optional[str]
    icon_url: Optional[str]
    banner_url: Optional[str]
    visibility: CommunityVisibility
    member_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CommunityMemberOut(BaseModel):
    user_id: UUID
    community_id: UUID
    role: CommunityRole

    model_config = {"from_attributes": True}