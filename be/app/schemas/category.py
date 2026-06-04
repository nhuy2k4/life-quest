from pydantic import BaseModel


class CategoryResponse(BaseModel):
	id: int
	slug: str
	name: str
	icon: str | None = None


class CategoryListResponse(BaseModel):
	items: list[CategoryResponse]
