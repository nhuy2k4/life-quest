from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorResponse(BaseModel):
    """Cấu trúc lỗi chuẩn hóa trả về cho client."""

    detail: str
    error_code: Optional[str] = None

    model_config = {"json_schema_extra": {"example": {"detail": "Resource not found", "error_code": "NOT_FOUND"}}}


class PaginatedResponse(BaseModel, Generic[T]):
    """Response có phân trang — dùng chung cho các list endpoints."""

    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_next=(page * page_size) < total,
        )
