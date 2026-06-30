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
    poi_distance_m: float | None,
    poi_required: bool = False,
) -> RuleResult:
    import re

    label_thresholds = {key.lower(): float(value) for key, value in (label_rules or {}).items()}
    matched_label = None
    matched_confidence = None

    # Combine labels from standard list AND special rules keys to form the complete set of allowed labels
    all_target_labels = set(quest_labels)
    if label_rules:
        all_target_labels.update(label_rules.keys())

    for label in all_target_labels:
        label_key = label.lower()
        threshold = label_thresholds.get(label_key, min_confidence)
        
        # Collect all scores from vision labels matching exactly or as a whole-word substring
        matching_scores = []
        for item in vision_labels:
            detected_label = item.get("label", "").lower()
            score = float(item.get("score", 0.0))
            
            if label_key == detected_label:
                matching_scores.append(score)
            else:
                # Use regex with word boundaries to match "hair" in "black hair", but not "car" in "cartoon"
                pattern = r'\b' + re.escape(label_key) + r'\b'
                if re.search(pattern, detected_label):
                    matching_scores.append(score)
                    
        if matching_scores:
            best_score = max(matching_scores)
            if best_score >= threshold:
                matched_label = label
                matched_confidence = best_score
                break

    if matched_label is None:
        return RuleResult(
            status="rejected",
            matched_label=None,
            confidence=None,
            poi_validated=False,
            reason="label_not_matched",
        )

    poi_ok = poi_distance_m is not None
    if poi_required and not poi_ok:
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
