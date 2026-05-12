from fastapi import Query
from pydantic import BaseModel
from typing import Generic, TypeVar, List

T = TypeVar("T")


class PageParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        limit: int = Query(20, ge=1, le=100, description="Items per page"),
    ):
        self.page = page
        self.limit = limit
        self.offset = (page - 1) * limit


class PagedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    limit: int
    has_next: bool

    @classmethod
    def create(cls, items: List[T], total: int, params: PageParams):
        return cls(
            items=items,
            total=total,
            page=params.page,
            limit=params.limit,
            has_next=(params.offset + params.limit) < total,
        )