from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from app.models.media import MediaType


class MediaOut(BaseModel):
    id: UUID
    url: str
    media_type: MediaType
    width: Optional[int]
    height: Optional[int]
    thumbnail_url: Optional[str]
    display_order: int

    model_config = {"from_attributes": True}