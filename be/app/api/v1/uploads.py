import asyncio
import logging
import re

import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.core.config import settings
from app.core.exceptions import BadRequestException
from app.deps.auth import get_current_user
from app.schemas.upload import UploadResponse

router = APIRouter(prefix="/uploads", tags=["Uploads"])
logger = logging.getLogger(__name__)


@router.post("/image", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    idempotency_key: str | None = Form(default=None),
    current_user=Depends(get_current_user),
) -> UploadResponse:
    if not settings.CLOUDINARY_CLOUD_NAME or not settings.CLOUDINARY_API_KEY or not settings.CLOUDINARY_API_SECRET:
        raise BadRequestException("Cloudinary is not configured")

    if not file.content_type or not file.content_type.startswith("image/"):
        raise BadRequestException("Only image uploads are allowed")

    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )

    # Đọc toàn bộ file vào memory trước để tránh race condition khi chạy
    # trong thread pool (SpooledTemporaryFile không thread-safe)
    file_bytes = await file.read()

    upload_options = {
        "folder": "lifequest",
        "resource_type": "image",
    }
    if idempotency_key:
        safe_key = re.sub(r"[^a-zA-Z0-9_-]", "", idempotency_key)[:80]
        if safe_key:
            upload_options.update(
                {
                    "public_id": f"{current_user.id}_{safe_key}",
                    "overwrite": True,
                    "invalidate": True,
                    "unique_filename": False,
                }
            )

    try:
        # cloudinary.uploader.upload() là synchronous/blocking — phải chạy
        # trong thread riêng để không block event loop của FastAPI
        result = await asyncio.to_thread(
            cloudinary.uploader.upload,
            file_bytes,
            **upload_options,
        )
    except Exception as exc:
        logger.exception("Cloudinary upload failed")
        raise BadRequestException("Upload failed") from exc

    url = result.get("secure_url") or result.get("url")
    public_id = result.get("public_id")

    if not url or not public_id:
        raise BadRequestException("Upload failed")

    return UploadResponse(url=url, public_id=public_id)
