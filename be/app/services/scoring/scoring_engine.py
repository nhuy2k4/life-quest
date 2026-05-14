from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreResult:
	ai_score: float
	rationale: dict[str, float]


def compute_ai_score(*, vision_score: float, rule_score: float, cheat_penalty: float) -> ScoreResult:
	base = (0.6 * vision_score) + (0.4 * rule_score)
	final_score = max(0.0, min(1.0, base - cheat_penalty))
	return ScoreResult(
		ai_score=final_score,
		rationale={
			"vision_score": vision_score,
			"rule_score": rule_score,
			"cheat_penalty": cheat_penalty,
		},
	)
