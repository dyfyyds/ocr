# ============================================================
#  分页辅助工具
# ============================================================
from typing import TypeVar, Generic
from pydantic import BaseModel

T = TypeVar("T")


class PageResponse(BaseModel):
    """统一分页响应结构。"""
    items: list
    total: int
    page: int
    size: int
    pages: int


def paginate(items: list, total: int, page: int, size: int) -> PageResponse:
    """封装分页响应。"""
    return PageResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size if size > 0 else 0,
    )
