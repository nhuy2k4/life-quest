from fastapi import APIRouter

from app.services.user.online_status_service import is_user_online

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/{user_id}/online", summary="Check user online status")
async def get_user_online_status(user_id: str) -> dict[str, str | bool]:
	"""Testing endpoint: checks Redis TTL-based online marker for a user."""
	return {
		"user_id": user_id,
		"is_online": await is_user_online(user_id),
	}
