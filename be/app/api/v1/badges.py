from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.deps.auth import CurrentUser, get_current_user
from app.deps.db import get_db
from app.schemas.badge import BadgeItem, BadgeListResponse, FeaturedBadgeResponse
from app.services.gamification.badge_service import BadgeService

router = APIRouter(prefix="/badges", tags=["Badges"])


def get_badge_service(db: AsyncSession = Depends(get_db)) -> BadgeService:
	return BadgeService(db)


@router.get("", response_model=BadgeListResponse)
async def list_badges(
	category: str | None = Query(default=None, description="Filter by category slug"),
	current_user: CurrentUser = Depends(get_current_user),
	service: BadgeService = Depends(get_badge_service),
) -> BadgeListResponse:
	"""Return all active badges with the current user's unlock status and progress."""
	return await service.get_badges_for_user(user_id=current_user.id, category=category)


@router.get("/featured", response_model=FeaturedBadgeResponse)
async def get_featured_badges(
	current_user: CurrentUser = Depends(get_current_user),
	service: BadgeService = Depends(get_badge_service),
) -> FeaturedBadgeResponse:
	"""Return the top featured badges to display on the profile header."""
	return await service.get_featured_badges(user_id=current_user.id)


@router.get("/{badge_id}", response_model=BadgeItem)
async def get_badge_detail(
	badge_id: uuid.UUID,
	current_user: CurrentUser = Depends(get_current_user),
	service: BadgeService = Depends(get_badge_service),
) -> BadgeItem:
	"""Return a single badge with progress details."""
	item = await service.get_badge_detail(user_id=current_user.id, badge_id=badge_id)
	if item is None:
		raise NotFoundException("Badge not found")
	return item
