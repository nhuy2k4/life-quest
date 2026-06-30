from __future__ import annotations

from dataclasses import dataclass

from app.services.vision.vision_service import VisionLabel


@dataclass(frozen=True)
class AntiCheatResult:
	is_suspicious: bool
	flags: dict[str, object]


def evaluate_anti_cheat(*, file_hash: str | None, labels: list[VisionLabel]) -> AntiCheatResult:
	# "display" is too broad and blocks any real photo taken near a monitor/TV
	suspicious_keywords = {"screenshot", "webpage", "monitor software"} 
	has_heavy_cheat_label = any(
		any(keyword in label.description.lower() for keyword in suspicious_keywords)
		for label in labels
	)
	
	# Screen present but might be background
	has_generic_screen = any(
		any(kw in label.description.lower() for kw in {"screen", "display"})
		for label in labels
	)

	flags: dict[str, object] = {
		"has_file_hash": bool(file_hash),
		"screen_like": has_generic_screen,
		"definite_screenshot": has_heavy_cheat_label
	}

	# In dev, we ONLY consider it suspicious if explicitly labeled a screenshot by vision
	return AntiCheatResult(is_suspicious=has_heavy_cheat_label, flags=flags)
