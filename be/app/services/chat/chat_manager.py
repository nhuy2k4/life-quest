import uuid
from collections import defaultdict

from fastapi import WebSocket


class ChatConnectionManager:
	def __init__(self) -> None:
		self._connections: dict[uuid.UUID, set[WebSocket]] = defaultdict(set)

	async def connect(self, *, user_id: uuid.UUID, websocket: WebSocket) -> None:
		await websocket.accept()
		self._connections[user_id].add(websocket)

	def disconnect(self, *, user_id: uuid.UUID, websocket: WebSocket) -> None:
		connections = self._connections.get(user_id)
		if not connections:
			return
		connections.discard(websocket)
		if not connections:
			self._connections.pop(user_id, None)

	async def send_to_user(self, *, user_id: uuid.UUID, payload: dict) -> None:
		for websocket in list(self._connections.get(user_id, set())):
			try:
				await websocket.send_json(payload)
			except Exception:
				self.disconnect(user_id=user_id, websocket=websocket)


chat_manager = ChatConnectionManager()
