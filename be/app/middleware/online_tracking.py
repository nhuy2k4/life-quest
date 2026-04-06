from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.user.online_status_service import mark_user_online_from_state


class OnlineTrackingMiddleware(BaseHTTPMiddleware):
    """
    Track user online presence by refreshing Redis TTL on each request.

    Key format: user:online:{user_id}
    Value: "1"
    TTL: 60 seconds
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Works with either request.state.user (object/dict) or request.state.user_id.
        await mark_user_online_from_state(
            user=getattr(request.state, "user", None),
            user_id=getattr(request.state, "user_id", None),
        )
        return response
