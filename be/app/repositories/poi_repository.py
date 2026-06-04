from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.poi import Poi


class PoiRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, poi_id: uuid.UUID) -> Poi | None:
        return await self.db.scalar(select(Poi).where(Poi.id == poi_id))

    async def get_max_active_radius_m(self) -> float | None:
        return await self.db.scalar(
            select(func.max(Poi.radius_m)).where(Poi.is_active.is_(True))
        )

    async def list_active_in_bbox(
        self,
        *,
        lat_min: float,
        lat_max: float,
        lng_min: float,
        lng_max: float,
    ) -> list[Poi]:
        stmt = (
            select(Poi)
            .where(Poi.is_active.is_(True))
            .where(Poi.latitude >= lat_min)
            .where(Poi.latitude <= lat_max)
            .where(Poi.longitude >= lng_min)
            .where(Poi.longitude <= lng_max)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
