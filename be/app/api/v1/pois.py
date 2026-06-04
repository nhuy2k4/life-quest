from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.db import get_db
from app.schemas.poi import PoiSuggestionResponse
from app.services.poi.poi_matcher import match_poi

router = APIRouter(prefix="/pois", tags=["POI"])


@router.get(
    "/suggest",
    response_model=PoiSuggestionResponse,
    summary="Suggest nearest POI for a GPS point",
)
async def suggest_poi(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    accuracy_m: float | None = Query(default=None, ge=0),
    db: AsyncSession = Depends(get_db),
) -> PoiSuggestionResponse:
    match = await match_poi(db=db, lat=lat, lng=lng, accuracy_m=accuracy_m)
    if match is None:
        return PoiSuggestionResponse(
            poi_id=None,
            name=None,
            poi_type=None,
            latitude=None,
            longitude=None,
            radius_m=None,
            distance_m=None,
        )

    poi = match.poi
    return PoiSuggestionResponse(
        poi_id=poi.id,
        name=poi.name,
        poi_type=poi.poi_type,
        latitude=poi.latitude,
        longitude=poi.longitude,
        radius_m=poi.radius_m,
        distance_m=match.distance_m,
    )
