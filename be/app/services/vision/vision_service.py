from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Iterable

import requests

from app.services.google_vision import create_vision_client


@dataclass(frozen=True)
class VisionLabel:
	description: str
	score: float


@dataclass(frozen=True)
class VisionResult:
	labels: list[VisionLabel]
	raw_response: dict | None

	@property
	def max_score(self) -> float:
		if not self.labels:
			return 0.0
		return max(label.score for label in self.labels)


class VisionService:
	def __init__(self) -> None:
		self.client = create_vision_client()

	def detect_labels_from_url(self, image_url: str, *, max_results: int = 20) -> VisionResult:
		content = self._download_image_bytes(image_url)
		from google.cloud import vision
		image = vision.Image(content=content)
		response = self.client.label_detection(image=image, max_results=max_results)

		if response.error.message:
			raise RuntimeError(response.error.message)

		labels = [VisionLabel(label.description, float(label.score)) for label in response.label_annotations]
		raw_response = self._serialize_response(response)
		return VisionResult(labels=labels, raw_response=raw_response)

	@staticmethod
	def _serialize_response(response: object) -> dict | None:
		serializer = getattr(response, "to_dict", None)
		if callable(serializer):
			return serializer()
		to_json = getattr(response, "to_json", None)
		if callable(to_json):
			try:
				return json.loads(to_json())
			except (TypeError, ValueError):
				return None
		return None

	@staticmethod
	def _download_image_bytes(image_url: str) -> bytes:
		response = requests.get(image_url, timeout=10)
		response.raise_for_status()
		return response.content


def serialize_labels(labels: Iterable[VisionLabel]) -> list[dict[str, float | str]]:
	return [{"label": label.description, "score": float(label.score)} for label in labels]
