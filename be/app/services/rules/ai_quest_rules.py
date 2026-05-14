from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuleResult:
    status: str
    matched_label: str | None
    confidence: float | None
    poi_validated: bool
    reason: str


def evaluate_ai_quest(
    *,
    quest_labels: list[str],
    label_rules: dict[str, float] | None,
    min_confidence: float,
    vision_labels: list[dict],
    poi_required: bool,
    poi_distance_m: float | None,
) -> RuleResult:
    label_scores = {item.get("label", "").lower(): float(item.get("score", 0.0)) for item in vision_labels}
    label_thresholds = {key.lower(): float(value) for key, value in (label_rules or {}).items()}
    matched_label = None
    matched_confidence = None

    # Combine labels from standard list AND special rules keys to form the complete set of allowed labels
    all_target_labels = set(quest_labels)
    if label_rules:
        all_target_labels.update(label_rules.keys())

    for label in all_target_labels:
        label_key = label.lower()
        score = label_scores.get(label_key)
        threshold = label_thresholds.get(label_key, min_confidence)
        if score is not None and score >= threshold:
            matched_label = label
            matched_confidence = score
            break

    if matched_label is None:
        return RuleResult(
            status="rejected",
            matched_label=None,
            confidence=None,
            poi_validated=False,
            reason="label_not_matched",
        )

    poi_ok = True
    if poi_required:
        poi_ok = poi_distance_m is not None

    if not poi_ok:
        return RuleResult(
            status="rejected",
            matched_label=matched_label,
            confidence=matched_confidence,
            poi_validated=False,
            reason="poi_required_missing",
        )

    return RuleResult(
        status="approved",
        matched_label=matched_label,
        confidence=matched_confidence,
        poi_validated=poi_ok,
        reason="ok",
    )
