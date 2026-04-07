from pydantic import BaseModel, Field


class PreferenceRequest(BaseModel):
	"""POST /users/me/preferences payload."""

	interests: list[int] = Field(default_factory=list)
	activity_level: str
	location_enabled: bool = True


class PreferenceResponse(BaseModel):
	"""Preference data returned to clients."""

	interests: list[int]
	interest_weights: dict
	activity_level: str | None = None
	location_enabled: bool
	notification_enabled: bool

	model_config = {"from_attributes": True}

