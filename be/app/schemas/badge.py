from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class BadgeProgress(BaseModel):
	current: int
	target: int


class BadgeItem(BaseModel):
	id: uuid.UUID
	name: str
	description: str
	icon_url: str
	rarity: str  # common | rare | epic | legendary
	category: str
	criteria: dict[str, Any]
	is_hidden: bool
	is_unlocked: bool
	unlocked_at: datetime | None = None
	progress: BadgeProgress

	model_config = {"from_attributes": True}


class BadgeListResponse(BaseModel):
	data: list[BadgeItem]
	total: int


class FeaturedBadge(BaseModel):
	id: uuid.UUID
	name: str
	icon_url: str
	rarity: str
	unlocked_at: datetime | None = None

	model_config = {"from_attributes": True}


class FeaturedBadgeResponse(BaseModel):
	data: list[FeaturedBadge]
