import uuid

import jwt
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CredentialsException
from app.core.security import decode_access_token, is_token_blacklisted
from app.deps.auth import CurrentUser, get_current_user
from app.deps.db import get_db
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.schemas.chat import (
	ChatActionResponse,
	ConversationCreateRequest,
	ConversationListResponse,
	ConversationResponse,
	MessageCreateRequest,
	MessageListResponse,
	MessageResponse,
)
from app.services.chat.chat_manager import chat_manager
from app.services.chat.chat_service import ChatService


router = APIRouter(prefix="/chat", tags=["Chat"])


def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
	return ChatService(db)


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=20, ge=1, le=100),
	current_user: CurrentUser = Depends(get_current_user),
	service: ChatService = Depends(get_chat_service),
) -> ConversationListResponse:
	items, total = await service.list_conversations(
		user_id=current_user.id,
		page=page,
		page_size=page_size,
	)
	return ConversationListResponse.create(items=items, total=total, page=page, page_size=page_size)


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def get_or_create_conversation(
	payload: ConversationCreateRequest,
	current_user: CurrentUser = Depends(get_current_user),
	service: ChatService = Depends(get_chat_service),
) -> ConversationResponse:
	return await service.get_or_create_conversation(
		user_id=current_user.id,
		target_user_id=payload.target_user_id,
	)


@router.get("/conversations/{conversation_id}/messages", response_model=MessageListResponse)
async def list_messages(
	conversation_id: uuid.UUID,
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=50, ge=1, le=100),
	current_user: CurrentUser = Depends(get_current_user),
	service: ChatService = Depends(get_chat_service),
) -> MessageListResponse:
	items, total = await service.list_messages(
		user_id=current_user.id,
		conversation_id=conversation_id,
		page=page,
		page_size=page_size,
	)
	return MessageListResponse.create(items=items, total=total, page=page, page_size=page_size)


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
	conversation_id: uuid.UUID,
	payload: MessageCreateRequest,
	current_user: CurrentUser = Depends(get_current_user),
	service: ChatService = Depends(get_chat_service),
) -> MessageResponse:
	message, recipient_id = await service.send_message(
		user_id=current_user.id,
		conversation_id=conversation_id,
		target_user_id=None,
		payload=payload,
	)
	await _broadcast_message(message=message, sender_id=current_user.id, recipient_id=recipient_id)
	return message


@router.post("/conversations/{conversation_id}/read", response_model=ChatActionResponse)
async def mark_conversation_read(
	conversation_id: uuid.UUID,
	current_user: CurrentUser = Depends(get_current_user),
	service: ChatService = Depends(get_chat_service),
) -> ChatActionResponse:
	read_count, other_user_id = await service.mark_read(user_id=current_user.id, conversation_id=conversation_id)
	await chat_manager.send_to_user(
		user_id=current_user.id,
		payload={"type": "conversation_read", "conversation_id": str(conversation_id), "read_count": read_count},
	)
	await chat_manager.send_to_user(
		user_id=other_user_id,
		payload={
			"type": "conversation_read",
			"conversation_id": str(conversation_id),
			"reader_id": str(current_user.id),
			"read_count": read_count,
		},
	)
	return ChatActionResponse()


@router.websocket("/ws")
async def chat_websocket(websocket: WebSocket, token: str = Query(default="")) -> None:
	current_user = await _authenticate_websocket(token)
	if current_user is None:
		await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
		return

	await chat_manager.connect(user_id=current_user.id, websocket=websocket)
	try:
		while True:
			payload = await websocket.receive_json()
			event_type = payload.get("type")
			if event_type == "message":
				await _handle_ws_message(current_user=current_user, payload=payload)
			elif event_type == "read":
				await _handle_ws_read(current_user=current_user, payload=payload)
			else:
				await websocket.send_json({"type": "error", "detail": "Unsupported chat event"})
	except WebSocketDisconnect:
		chat_manager.disconnect(user_id=current_user.id, websocket=websocket)
	except Exception as exc:
		await websocket.send_json({"type": "error", "detail": str(exc)})
		chat_manager.disconnect(user_id=current_user.id, websocket=websocket)


async def _handle_ws_message(*, current_user: CurrentUser, payload: dict) -> None:
	conversation_id = payload.get("conversation_id")
	target_user_id = payload.get("target_user_id")
	content = payload.get("content")
	message_payload = MessageCreateRequest(content=content)

	async with AsyncSessionLocal() as db:
		service = ChatService(db)
		message, recipient_id = await service.send_message(
			user_id=current_user.id,
			conversation_id=uuid.UUID(conversation_id) if conversation_id else None,
			target_user_id=uuid.UUID(target_user_id) if target_user_id else None,
			payload=message_payload,
		)

	await _broadcast_message(message=message, sender_id=current_user.id, recipient_id=recipient_id)


async def _handle_ws_read(*, current_user: CurrentUser, payload: dict) -> None:
	conversation_id = uuid.UUID(payload.get("conversation_id"))
	async with AsyncSessionLocal() as db:
		service = ChatService(db)
		read_count, other_user_id = await service.mark_read(user_id=current_user.id, conversation_id=conversation_id)

	await chat_manager.send_to_user(
		user_id=current_user.id,
		payload={"type": "conversation_read", "conversation_id": str(conversation_id), "read_count": read_count},
	)
	await chat_manager.send_to_user(
		user_id=other_user_id,
		payload={
			"type": "conversation_read",
			"conversation_id": str(conversation_id),
			"reader_id": str(current_user.id),
			"read_count": read_count,
		},
	)


async def _broadcast_message(*, message: MessageResponse, sender_id: uuid.UUID, recipient_id: uuid.UUID) -> None:
	message_payload = jsonable_encoder(message)
	await chat_manager.send_to_user(
		user_id=sender_id,
		payload={"type": "message", "message": {**message_payload, "is_mine": True}},
	)
	await chat_manager.send_to_user(
		user_id=recipient_id,
		payload={"type": "message", "message": {**message_payload, "is_mine": False}},
	)


async def _authenticate_websocket(token: str) -> CurrentUser | None:
	if not token:
		return None
	try:
		payload = decode_access_token(token)
	except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, CredentialsException):
		return None
	if await is_token_blacklisted(payload):
		return None

	user_id = payload.get("sub")
	if not user_id:
		return None

	async with AsyncSessionLocal() as db:
		user = await db.scalar(select(User).where(User.id == uuid.UUID(user_id)))
		if user is None or user.is_banned:
			return None
		return CurrentUser(
			id=user.id,
			role=user.role,
			onboarding_completed=user.onboarding_completed,
			is_banned=user.is_banned,
		)
