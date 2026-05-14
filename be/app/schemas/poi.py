import uuid
from pydantic import BaseModel


class PoiSuggestionResponse(BaseModel):
    poi_id: uuid.UUID | None
    name: str | None
    poi_type: str | None
    latitude: float | None
    longitude: float | None
    radius_m: float | None
    distance_m: float | None
