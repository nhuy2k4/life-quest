from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.models.submission import Submission
from app.services.rules.anti_cheat_rules import AntiCheatResult, evaluate_anti_cheat
from app.services.rules.ai_quest_rules import RuleResult, evaluate_ai_quest
from app.services.scoring.scoring_engine import ScoreResult, compute_ai_score
from app.services.vision.vision_service import VisionResult, VisionService, serialize_labels


class ApprovalDecisionType(StrEnum):
	APPROVE = "approve"
	REJECT = "reject"
	MANUAL_REVIEW = "manual_review"


@dataclass(frozen=True)
class ApprovalDecision:
	decision: ApprovalDecisionType
	ai_score: float
	is_suspicious: bool
	cheat_flags: dict[str, object]
	vision_labels: list[dict[str, float | str]]
	vision_raw: dict | None
	vision_max_score: float
	ai_metadata: dict[str, object]


class AIApprovalService:
	def __init__(self, *, vision_service: VisionService | None = None) -> None:
		self.vision_service = vision_service or VisionService()

	def evaluate_submission(self, submission: Submission) -> ApprovalDecision:
		try:
			vision_result = self.vision_service.detect_labels_from_url(submission.image_url)
		except Exception as exc:
			return self._manual_review_for_error(error=exc)

		quest = submission.user_quest.quest if submission.user_quest else None
		quest_labels = quest.labels if quest and quest.labels else []
		label_rules = quest.label_rules if quest else None
		min_confidence = float(quest.min_confidence or 0.5) if quest else 0.5
		poi_required = bool(quest.poi_required) if quest else False

		rule_result = evaluate_ai_quest(
			quest_labels=quest_labels,
			label_rules=label_rules,
			min_confidence=min_confidence,
			vision_labels=serialize_labels(vision_result.labels),
			poi_required=poi_required,
			poi_distance_m=submission.poi_distance_m,
		)
		anti_cheat_result = evaluate_anti_cheat(file_hash=submission.file_hash, labels=vision_result.labels)
		score_result = compute_ai_score(
			vision_score=vision_result.max_score,
			rule_score=1.0 if rule_result.status == "approved" else 0.0,
			cheat_penalty=0.2 if anti_cheat_result.is_suspicious else 0.0,
		)

		decision = self._decide(rule_result.status, anti_cheat_result)
		cheat_flags = self._build_flags(vision_result, rule_result, anti_cheat_result, score_result)
		ai_metadata = {
			"matched_label": rule_result.matched_label,
			"confidence": rule_result.confidence,
			"poi_validated": rule_result.poi_validated,
			"reason": rule_result.reason,
		}
		return ApprovalDecision(
			decision=decision,
			ai_score=score_result.ai_score,
			is_suspicious=anti_cheat_result.is_suspicious,
			cheat_flags=cheat_flags,
			vision_labels=serialize_labels(vision_result.labels),
			vision_raw=vision_result.raw_response,
			vision_max_score=vision_result.max_score,
			ai_metadata=ai_metadata,
		)

	@staticmethod
	def _decide(rule_status: str, anti_cheat_result: AntiCheatResult) -> ApprovalDecisionType:
		if anti_cheat_result.is_suspicious:
			return ApprovalDecisionType.MANUAL_REVIEW
		if rule_status == "approved":
			return ApprovalDecisionType.APPROVE
		return ApprovalDecisionType.REJECT

	@staticmethod
	def _build_flags(
		vision_result: VisionResult,
		rule_result: RuleResult,
		anti_cheat_result: AntiCheatResult,
		score_result: ScoreResult,
	) -> dict[str, object]:
		return {
			"vision_labels": serialize_labels(vision_result.labels),
			"matched_label": rule_result.matched_label,
			"rule_status": rule_result.status,
			"anti_cheat": anti_cheat_result.flags,
			"score_rationale": score_result.rationale,
		}

	@staticmethod
	def _manual_review_for_error(*, error: Exception) -> ApprovalDecision:
		return ApprovalDecision(
			decision=ApprovalDecisionType.MANUAL_REVIEW,
			ai_score=0.0,
			is_suspicious=True,
			cheat_flags={"vision_error": str(error)},
			vision_labels=[],
			vision_raw=None,
			vision_max_score=0.0,
			ai_metadata={"reason": "vision_error"},
		)
