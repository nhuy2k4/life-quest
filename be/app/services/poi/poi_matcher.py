from __future__ import annotations

import json
import math
from dataclasses import dataclass
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import redis_get, redis_set
from app.models.poi import Poi
from app.repositories.poi_repository import PoiRepository


@dataclass(frozen=True)
class PoiMatch:
    poi: Poi
    distance_m: float


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


def _bbox(lat: float, lng: float, radius_m: float) -> tuple[float, float, float, float]:
    lat_delta = radius_m / 111000.0
    lng_delta = radius_m / (111000.0 * max(0.1, math.cos(math.radians(lat))))
    return (lat - lat_delta, lat + lat_delta, lng - lng_delta, lng + lng_delta)


def _cache_key(lat: float, lng: float) -> str:
    return f"poi:suggest:{round(lat, settings.POI_CACHE_ROUNDING)}:{round(lng, settings.POI_CACHE_ROUNDING)}"


async def match_poi(
    *,
    db: AsyncSession,
    lat: float,
    lng: float,
    accuracy_m: float | None = None,
) -> PoiMatch | None:
    cache_key = _cache_key(lat, lng)
    cached = await redis_get(cache_key)
    repository = PoiRepository(db)

    if cached:
        try:
            payload = json.loads(cached)
            poi_id = payload.get("poi_id")
            distance_m = payload.get("distance_m")
            if poi_id and distance_m is not None:
                try:
                    poi_uuid = uuid.UUID(str(poi_id))
                except (TypeError, ValueError):
                    poi_uuid = None
                poi = await repository.get_by_id(poi_uuid) if poi_uuid else None
                if poi is not None and poi.is_active:
                    return PoiMatch(poi=poi, distance_m=float(distance_m))
        except (ValueError, TypeError):
            pass

    accuracy_buffer_m = min(max(float(accuracy_m or 0), 0.0), settings.POI_MAX_RADIUS_M)
    max_poi_radius_m = await repository.get_max_active_radius_m()
    search_radius_m = max(settings.POI_MAX_RADIUS_M, float(max_poi_radius_m or 0) + accuracy_buffer_m)
    lat_min, lat_max, lng_min, lng_max = _bbox(lat, lng, search_radius_m)
    candidates = await repository.list_active_in_bbox(
        lat_min=lat_min,
        lat_max=lat_max,
        lng_min=lng_min,
        lng_max=lng_max,
    )

    best: PoiMatch | None = None
    for poi in candidates:
        distance_m = _haversine_m(lat, lng, poi.latitude, poi.longitude)
        if distance_m <= float(poi.radius_m or 0) + accuracy_buffer_m:
            if best is None or distance_m < best.distance_m:
                best = PoiMatch(poi=poi, distance_m=distance_m)

    if best is not None:
        await redis_set(
            cache_key,
            json.dumps({"poi_id": str(best.poi.id), "distance_m": best.distance_m}),
            ttl=settings.POI_CACHE_TTL_SECONDS,
        )

    return best
