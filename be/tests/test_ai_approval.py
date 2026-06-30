"""Unit tests for AI approval logic."""

import uuid

from app.models.enums import UserQuestStatus
from app.models.quest import Quest
from app.models.submission import Submission
from app.models.user_quest import UserQuest
from app.services.ai.ai_approval_service import AIApprovalService, ApprovalDecisionType
from app.services.vision.vision_service import VisionLabel, VisionResult


class FakeVisionService:
    def __init__(self, labels: list[VisionLabel]) -> None:
        self._result = VisionResult(labels=labels, raw_response=None)

    def detect_labels_from_url(self, image_url: str, *, max_results: int = 10) -> VisionResult:
        return self._result


def _build_submission(
    *,
    title: str,
    description: str,
    image_url: str,
    file_hash: str,
    labels: list[str] | None = None,
    min_confidence: float = 0.5,
) -> Submission:
    quest_id = uuid.uuid4()
    user_id = uuid.uuid4()

    quest = Quest(
        id=quest_id,
        title=title,
        description=description,
        xp_reward=100,
        difficulty="easy",
        approval_rate=1.0,
        time_limit_hours=24,
        location_required=False,
        is_active=True,
        labels=labels,
        min_confidence=min_confidence,
    )
    user_quest = UserQuest(
        user_id=user_id,
        quest_id=quest_id,
        status=UserQuestStatus.SUBMITTED,
        quest=quest,
    )
    return Submission(
        user_quest_id=uuid.uuid4(),
        image_url=image_url,
        cloudinary_public_id="sample",
        file_hash=file_hash,
        user_quest=user_quest,
    )


def test_ai_approval_auto_approve_high_score():
    labels = [
        VisionLabel("morning", 0.9),
        VisionLabel("outdoor", 0.85),
        VisionLabel("training", 0.8),
    ]
    submission = _build_submission(
        title="Morning Run",
        description="Outdoor training session",
        image_url="https://example.com/image.jpg",
        file_hash="a" * 32,
        labels=["morning"],
    )
    service = AIApprovalService(vision_service=FakeVisionService(labels))

    decision = service.evaluate_submission(submission)

    assert decision.decision == ApprovalDecisionType.APPROVE
    assert decision.ai_score >= 0.0


def test_ai_approval_manual_review_low_score():
    labels = [
        VisionLabel("random", 0.2),
    ]
    submission = _build_submission(
        title="Morning Run",
        description="Outdoor training session",
        image_url="https://example.com/image.jpg",
        file_hash="b" * 32,
    )
    service = AIApprovalService(vision_service=FakeVisionService(labels))

    decision = service.evaluate_submission(submission)

    assert decision.decision == ApprovalDecisionType.REJECT


def test_ai_approval_manual_review_suspicious_label():
    labels = [
        VisionLabel("screenshot", 0.95),
        VisionLabel("screen", 0.9),
    ]
    submission = _build_submission(
        title="Morning Run",
        description="Outdoor training session",
        image_url="https://example.com/image.jpg",
        file_hash="c" * 32,
    )
    service = AIApprovalService(vision_service=FakeVisionService(labels))

    decision = service.evaluate_submission(submission)

    assert decision.decision == ApprovalDecisionType.MANUAL_REVIEW
    assert decision.is_suspicious is True


def test_ai_approval_substring_label_matching():
    # Detect 'black hair' which contains whole word 'hair'
    labels = [
        VisionLabel("black hair", 0.95),
        VisionLabel("t-shirt", 0.9),
    ]
    submission = _build_submission(
        title="People shot",
        description="Take a photo of a person",
        image_url="https://example.com/image.jpg",
        file_hash="d" * 32,
        labels=["hair"],
    )
    service = AIApprovalService(vision_service=FakeVisionService(labels))

    decision = service.evaluate_submission(submission)

    assert decision.decision == ApprovalDecisionType.APPROVE
    assert decision.ai_metadata["matched_label"] == "hair"
    assert decision.ai_metadata["confidence"] == 0.95


def test_ai_approval_substring_label_no_false_positive():
    # Detect 'cartoon' which contains 'car' but not as a whole word
    labels = [
        VisionLabel("cartoon", 0.95),
    ]
    submission = _build_submission(
        title="Car shot",
        description="Take a photo of a car",
        image_url="https://example.com/image.jpg",
        file_hash="e" * 32,
        labels=["car"],
    )
    service = AIApprovalService(vision_service=FakeVisionService(labels))

    decision = service.evaluate_submission(submission)

    assert decision.decision == ApprovalDecisionType.REJECT


def test_ai_approval_anti_cheat_concatenation_no_false_positive():
    # Detect 'computer monitor' and 'software engineering'
    # which when joined could collide to match 'monitor software'
    labels = [
        VisionLabel("computer monitor", 0.95),
        VisionLabel("software engineering", 0.9),
    ]
    submission = _build_submission(
        title="Coding",
        description="Write code",
        image_url="https://example.com/image.jpg",
        file_hash="f" * 32,
        labels=["computer monitor"],
    )
    service = AIApprovalService(vision_service=FakeVisionService(labels))

    decision = service.evaluate_submission(submission)

    assert decision.cheat_flags["anti_cheat"]["definite_screenshot"] is False
    assert decision.is_suspicious is False
