import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.deps.auth import CurrentUser, get_current_user
from app.deps.db import get_db
from app.models.user import User
from app.schemas.user import UserMeResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
	"/me",
	response_model=UserMeResponse,
	summary="Lấy thông tin user hiện tại",
	description="Yêu cầu access token hợp lệ. Trả về profile đầy đủ của user đang đăng nhập.",
)
async def get_me(
	current_user: CurrentUser = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> UserMeResponse:
	user = await db.scalar(select(User).where(User.id == uuid.UUID(str(current_user.id))))
	if user is None:
		raise NotFoundException("User không tồn tại")
	return user
