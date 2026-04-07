from fastapi import APIRouter

from app.services.user.online_status_service import is_user_online
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.auth import CurrentUser, get_current_user
from app.deps.db import get_db
from app.schemas.preference import PreferenceRequest, PreferenceResponse
from app.schemas.user import UserMeDataResponse, UserMeResponse
from app.schemas.user import UpdateProfileRequest
from app.services.user.preference_service import PreferenceService
from app.services.user.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/{user_id}/online", summary="Check user online status")
async def get_user_online_status(user_id: str) -> dict[str, str | bool]:
	"""Testing endpoint: checks Redis TTL-based online marker for a user."""
	return {
		"user_id": user_id,
		"is_online": await is_user_online(user_id),
	}
def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
	return UserService(db)


def get_preference_service(db: AsyncSession = Depends(get_db)) -> PreferenceService:
	return PreferenceService(db)


@router.get(
	"/me",
	response_model=UserMeDataResponse,
	summary="Lấy thông tin user hiện tại",
	description="Yêu cầu access token hợp lệ. Trả về profile đầy đủ của user đang đăng nhập.",
)
async def get_me(
	current_user: CurrentUser = Depends(get_current_user),
	service: UserService = Depends(get_user_service),
) -> UserMeDataResponse:
	user = await service.get_me(current_user.id)
	return UserMeDataResponse(data=UserMeResponse.model_validate(user))


@router.patch(
	"/me",
	summary="Cập nhật profile user hiện tại",
	description="Cập nhật username/email của user đang đăng nhập.",
)
async def update_me(
	payload: UpdateProfileRequest,
	current_user: CurrentUser = Depends(get_current_user),
	service: UserService = Depends(get_user_service),
) -> dict[str, UserMeResponse]:
	user = await service.update_me(current_user.id, payload)
	return {"data": UserMeResponse.model_validate(user)}


@router.post(
	"/me/preferences",
	summary="Tạo hoặc cập nhật preferences của user",
	description="Lưu preferences, đánh dấu onboarding_completed=true và invalidate cache recommendation.",
)
async def update_my_preferences(
	payload: PreferenceRequest,
	current_user: CurrentUser = Depends(get_current_user),
	service: PreferenceService = Depends(get_preference_service),
) -> dict[str, PreferenceResponse]:
	preference = await service.update_my_preferences(current_user.id, payload)
	return {"data": PreferenceResponse.model_validate(preference)}


@router.get(
	"/me/preferences",
	summary="Lấy preferences của user hiện tại",
)
async def get_my_preferences(
	current_user: CurrentUser = Depends(get_current_user),
	service: PreferenceService = Depends(get_preference_service),
) -> dict[str, PreferenceResponse]:
	preference = await service.get_my_preferences(current_user.id)
	return {"data": PreferenceResponse.model_validate(preference)}
