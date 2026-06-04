from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.db import get_db
from app.models.quest import Category
from app.schemas.category import CategoryListResponse, CategoryResponse

router = APIRouter(prefix="/categories", tags=["Categories"])


def _fallback_slug(category: Category) -> str:
	if category.slug:
		return category.slug
	return category.name.strip().lower().replace(" ", "-")


@router.get("", response_model=CategoryListResponse)
async def list_categories(db: AsyncSession = Depends(get_db)) -> CategoryListResponse:
	rows = await db.scalars(select(Category).order_by(Category.id.asc()))
	items = [
		CategoryResponse(
			id=category.id,
			slug=_fallback_slug(category),
			name=category.name,
			icon=category.icon,
		)
		for category in rows.all()
	]
	return CategoryListResponse(items=items)
