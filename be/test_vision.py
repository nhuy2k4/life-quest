import os
from pathlib import Path

import pytest
from google.cloud import vision
from dotenv import load_dotenv
load_dotenv()

from app.services.google_vision import create_vision_client


def test_image() -> None:
    if os.getenv("RUN_VISION_TESTS") != "1":
        pytest.skip("Vision integration test is opt-in (set RUN_VISION_TESTS=1).")

    client = create_vision_client()

    image_path = Path(__file__).resolve().parent / "test.jpg"
    with image_path.open("rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = client.label_detection(image=image)

    if response.error.message:
        raise RuntimeError(response.error.message)

    for label in response.label_annotations:
        print(f"{label.description}: {label.score:.2f}")


if __name__ == "__main__":
    test_image()