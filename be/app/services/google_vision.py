from __future__ import annotations

import logging
import os
from typing import Optional

from dotenv import load_dotenv
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import vision
from google.oauth2 import service_account

from app.core.config import settings

logger = logging.getLogger("lifequest.google_vision")


def configure_google_vision() -> tuple[Optional[str], Optional[str]]:
    load_dotenv()
    desired_path = settings.GOOGLE_APPLICATION_CREDENTIALS.strip() or None

    # Tự động fallback về file local nếu đường dẫn cấu hình không tồn tại để tránh nhận nhầm path global Windows
    if (not desired_path or not os.path.exists(desired_path)) and os.path.exists("google-vision.json"):
        desired_path = "google-vision.json"
        logger.info("FALLBACK: Using local vision key file: google-vision.json")

    if desired_path:
        # Force overwrite env variable
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(desired_path)
        active_path = os.path.abspath(desired_path)
    else:
        active_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not active_path:
        raise DefaultCredentialsError("GOOGLE_APPLICATION_CREDENTIALS is not set")

    credentials = service_account.Credentials.from_service_account_file(active_path)
    project_id = credentials.project_id

    logger.info("Google Vision credentials path: %s", active_path)
    logger.info("Google Vision project_id: %s", project_id or "<unknown>")
    return active_path, project_id


def create_vision_client() -> vision.ImageAnnotatorClient:
    active_path, _ = configure_google_vision()
    credentials = service_account.Credentials.from_service_account_file(active_path)
    return vision.ImageAnnotatorClient(credentials=credentials)
