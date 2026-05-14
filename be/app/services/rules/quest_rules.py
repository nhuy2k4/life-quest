from __future__ import annotations

from dataclasses import dataclass

from app.services.vision.vision_service import VisionLabel


@dataclass(frozen=True)
class QuestRuleResult:
	match_score: float
	matched_keywords: list[str]


DEFAULT_MIN_CONFIDENCE = 0.6


def evaluate_quest_match(
	*,
	quest_title: str,
	quest_description: str | None,
	quest_labels: list[str] | None,
	label_rules: dict[str, float] | None,
	min_confidence: float | None,
	labels: list[VisionLabel],
) -> QuestRuleResult:
	if quest_labels:
		normalized_targets = [item.strip().lower() for item in quest_labels if item.strip()]
		label_scores = {label.description.lower(): label.score for label in labels}
		matched: list[str] = []
		threshold_default = min_confidence or DEFAULT_MIN_CONFIDENCE

		for target in normalized_targets:
			threshold = threshold_default
			if label_rules and target in label_rules:
				threshold = float(label_rules[target])
			score = label_scores.get(target)
			if score is not None and score >= threshold:
				matched.append(target)

		if not matched:
			return QuestRuleResult(match_score=0.0, matched_keywords=[])

		match_ratio = len(set(matched)) / max(1, len(set(normalized_targets)))
		match_score = min(1.0, 0.4 + (0.6 * match_ratio))
		return QuestRuleResult(match_score=match_score, matched_keywords=sorted(set(matched)))

	keywords = _extract_keywords(quest_title, quest_description)
	label_text = " ".join(label.description.lower() for label in labels)

	matched = [keyword for keyword in keywords if keyword in label_text]
	if not matched:
		return QuestRuleResult(match_score=0.0, matched_keywords=[])

	match_score = min(1.0, 0.4 + (0.1 * len(set(matched))))
	return QuestRuleResult(match_score=match_score, matched_keywords=sorted(set(matched)))


def _extract_keywords(title: str, description: str | None) -> list[str]:
	raw = f"{title} {description or ''}".lower()
	tokens = [token.strip() for token in raw.replace("-", " ").split()]
	return [token for token in tokens if len(token) >= 4]
