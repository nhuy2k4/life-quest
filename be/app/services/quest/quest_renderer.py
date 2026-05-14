from __future__ import annotations


def render_quest_text(template: str | None, labels: list[str] | None, poi_name: str | None) -> str:
    base_template = template or "Take a photo of a {label}"
    safe_labels = [label for label in (labels or []) if label]
    label = safe_labels[0] if safe_labels else "object"
    text = base_template.replace("{label}", label)
    if poi_name:
        return f"{text} at {poi_name}"
    return text
