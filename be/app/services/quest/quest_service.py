from datetime import datetime, timedelta, timezone
from uuid import UUID

import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import BadRequestException, ConflictException, ForbiddenException, NotFoundException
from app.models.enums import EventStatus, PostVisibility, SubmissionStatus, UserQuestStatus
from app.models.event import Event, EventQuest
from app.models.user_quest import STARTED_STATUSES
from app.repositories.quest_repository import QuestRepository
from app.schemas.quest import (
    QuestDetailResponse,
    QuestListItemResponse,
    StartQuestResponse,
    SubmitQuestRequest,
    SubmitQuestResponse,
)
from app.services.quest.quest_renderer import render_quest_text
from app.services.pipeline.approval_pipeline import enqueue_submission_approval
from app.services.vision.vision_service import VisionService


logger = logging.getLogger(__name__)

MAX_SUBMISSION_RETRY_COUNT = 3


class QuestService:
    """Quest business logic with strict state-transition checks."""

    def __init__(self, repository: QuestRepository) -> None:
        self.repository = repository

    async def list_quests(self, *, user_id: UUID, page: int, page_size: int) -> tuple[list[QuestListItemResponse], int]:
        offset = (page - 1) * page_size
        quests, total = await self.repository.list_active_quests(offset=offset, limit=page_size)
        since = datetime.now(timezone.utc) - timedelta(days=7)
        image_map = await self.repository.get_top_post_images_for_quests(
            quest_ids=[quest.id for quest in quests],
            since=since,
        )

        items: list[QuestListItemResponse] = []
        for quest in quests:
            image_url = quest.image_url or image_map.get(quest.id)
            user_quest = await self.repository.get_user_quest(
                user_id=user_id,
                quest_id=quest.id,
                poi_id=None,
            )
            items.append(
                QuestListItemResponse(
                    id=quest.id,
                    poi_id=None,
                    image_url=image_url,
                    rendered_text=render_quest_text(quest.template, quest.labels, None),
                    labels=quest.labels or [],
                    min_confidence=float(quest.min_confidence or 0.5),
                    xp_reward=quest.xp_reward,
                    is_active=quest.is_active,
                    user_status=user_quest.normalized_status if user_quest else UserQuestStatus.NOT_STARTED,
                )
            )

        return items, total

    async def list_quest_log(self, *, user_id: UUID) -> tuple[list[QuestListItemResponse], int]:
        quests, _ = await self.repository.list_active_quests(offset=0, limit=500)
        user_instances = await self.repository.list_user_quest_instances(user_id=user_id)
        quest_ids = list({quest.id for quest in quests} | {quest.id for _, quest, _ in user_instances})
        since = datetime.now(timezone.utc) - timedelta(days=7)
        image_map = await self.repository.get_top_post_images_for_quests(
            quest_ids=quest_ids,
            since=since,
        )

        items: list[QuestListItemResponse] = []
        for quest in quests:
            image_url = quest.image_url or image_map.get(quest.id)
            user_quest = await self.repository.get_user_quest(
                user_id=user_id,
                quest_id=quest.id,
                poi_id=None,
            )
            items.append(
                QuestListItemResponse(
                    id=quest.id,
                    poi_id=None,
                    poi_name=None,
                    image_url=image_url,
                    rendered_text=render_quest_text(quest.template, quest.labels, None),
                    labels=quest.labels or [],
                    min_confidence=float(quest.min_confidence or 0.5),
                    xp_reward=quest.xp_reward,
                    is_active=quest.is_active,
                    user_status=user_quest.normalized_status if user_quest else UserQuestStatus.NOT_STARTED,
                )
            )

        for user_quest, quest, poi in user_instances:
            poi_name = poi.name if poi else None
            base_xp = quest.xp_reward
            poi_bonus_xp = round(base_xp * 0.5)
            items.append(
                QuestListItemResponse(
                    id=quest.id,
                    poi_id=user_quest.poi_id,
                    poi_name=poi_name,
                    image_url=quest.image_url or image_map.get(quest.id),
                    rendered_text=render_quest_text(quest.template, quest.labels, poi_name),
                    labels=quest.labels or [],
                    min_confidence=float(quest.min_confidence or 0.5),
                    xp_reward=base_xp + poi_bonus_xp,
                    is_active=quest.is_active,
                    user_status=user_quest.normalized_status,
                )
            )

        return items, len(items)

    async def get_quest_detail(
    self,
    *,
    user_id: UUID,
    quest_id: UUID,
    poi_id: UUID | None = None,
    ) -> QuestDetailResponse:
        quest = await self.repository.get_quest_by_id(quest_id)

        if quest is None or not quest.is_active:
            raise NotFoundException("Quest không tồn tại")

        poi = None
        poi_name = None

        if poi_id is not None:
            poi = await self.repository.get_poi_by_id(poi_id)

            if poi is None:
                raise NotFoundException("Vị trí không tồn tại")

            poi_name = poi.name

        user_quest = await self.repository.get_user_quest(
            user_id=user_id,
            quest_id=quest_id,
            poi_id=poi_id,
        )

        detail_poi_id = poi_id

        rendered_text = render_quest_text(
            quest.template,
            quest.labels,
            poi_name,
        )

        image_map = await self.repository.get_top_post_images_for_quests(
            quest_ids=[quest.id],
            since=datetime.now(timezone.utc) - timedelta(days=7),
        )
        image_url = quest.image_url or image_map.get(quest.id)

        base_xp = quest.xp_reward

        # Dynamically detect if quest belongs to any event (more reliable than the is_event column)
        linked_event_id = await self.repository.db.scalar(
            select(EventQuest.event_id).where(EventQuest.quest_id == quest_id).limit(1)
        )
        is_event_quest = quest.is_event or (linked_event_id is not None)

        event_id = None
        event_location_name = None
        event_latitude = None
        event_longitude = None
        event_radius_m = None

        if linked_event_id is not None:
            from app.models.event import Event
            event_obj = await self.repository.db.scalar(
                select(Event).where(Event.id == linked_event_id)
            )
            if event_obj:
                event_id = event_obj.id
                event_location_name = event_obj.location_name
                event_latitude = event_obj.latitude
                event_longitude = event_obj.longitude
                event_radius_m = event_obj.radius_m

        # Event quests don't use POI — only GPS check-in area is validated at submit time
        if is_event_quest:
            detail_poi_id = None
            poi_name = None
            poi_required = False
            poi_bonus_xp = 0
        else:
            poi_required = bool(
                detail_poi_id is not None
                or quest.location_required
            )
            poi_bonus_xp = (
                round(base_xp * 0.5)
                if poi_required
                else 0
            )

        total_xp_with_poi = base_xp + poi_bonus_xp

        return QuestDetailResponse(
            id=quest.id,

            poi_id=detail_poi_id,
            poi_name=poi_name,
            image_url=image_url,

            rendered_text=rendered_text,
            description=quest.description,

            labels=quest.labels or [],
            min_confidence=float(quest.min_confidence or 0.5),

            xp_reward=base_xp,
            base_xp=base_xp,
            poi_bonus_xp=poi_bonus_xp,
            total_xp_with_poi=total_xp_with_poi,

            poi_required=poi_required,
            is_active=quest.is_active,
            is_event=is_event_quest,

            user_status=(
                user_quest.normalized_status
                if user_quest
                else UserQuestStatus.NOT_STARTED
            ),

            started_at=(
                user_quest.started_at
                if user_quest
                else None
            ),
            event_id=event_id,
            event_location_name=event_location_name,
            event_latitude=event_latitude,
            event_longitude=event_longitude,
            event_radius_m=event_radius_m,
        )

    async def start_quest(
        self,
        *,
        user_id: UUID,
        onboarding_completed: bool,
        quest_id: UUID,
        poi_id: UUID | None = None,
    ) -> StartQuestResponse:
        if not onboarding_completed:
            raise ForbiddenException("Báº¡n cáº§n hoÃ n táº¥t onboarding trÆ°á»›c khi báº¯t Ä‘áº§u quest")

        quest = await self.repository.get_quest_by_id(quest_id)
        if quest is None or not quest.is_active:
            raise NotFoundException("Quest khÃ´ng tá»“n táº¡i")
        now = datetime.now(timezone.utc)

        # Check if this quest belongs to an active event
        active_event_id = await self.repository.db.scalar(
            select(Event.id)
            .join(EventQuest, EventQuest.event_id == Event.id)
            .where(
                EventQuest.quest_id == quest_id,
                Event.status == EventStatus.ACTIVE,
                Event.start_at <= now,
                Event.end_at >= now,
            )
            .order_by(Event.start_at.desc())
            .limit(1)
        )

        if not quest.location_required or active_event_id:
            poi_id = None
        user_quest = await self.repository.get_user_quest(user_id=user_id, quest_id=quest_id, poi_id=poi_id)

        if user_quest is not None:
            if user_quest.normalized_status == UserQuestStatus.STARTED:
                return StartQuestResponse(
                    user_quest_id=user_quest.id,
                    quest_id=quest.id,
                    poi_id=user_quest.poi_id,
                    status=UserQuestStatus.STARTED,
                    started_at=user_quest.started_at,
                )
            if user_quest.normalized_status == UserQuestStatus.APPROVED:
                raise ConflictException("Quest đã hoàn thành trước đó")
            if user_quest.normalized_status == UserQuestStatus.SUBMITTED and not active_event_id:
                raise ConflictException("Quest đã được nộp hoặc đã hoàn thành trước đó")
            if user_quest.normalized_status == UserQuestStatus.REJECTED:
                existing_submission = await self.repository.get_submission_by_user_quest_id(user_quest.id)
                if existing_submission is not None and existing_submission.retry_count >= MAX_SUBMISSION_RETRY_COUNT:
                    raise ConflictException("Bạn đã hết số lần cập nhật ảnh cho quest này")
                # Còn lượt retry — cho phép user submit ảnh mới, trả về status REJECTED
                # để frontend biết đây là flow retry (không cần start lại)
                return StartQuestResponse(
                    user_quest_id=user_quest.id,
                    quest_id=quest.id,
                    poi_id=user_quest.poi_id,
                    status=UserQuestStatus.REJECTED,
                    started_at=user_quest.started_at,
                )

            user_quest.status = UserQuestStatus.STARTED
            user_quest.started_at = now
            if poi_id is not None:
                await self.repository.create_quest_instance_mapping(
                    user_id=user_id,
                    quest_id=quest.id,
                    poi_id=poi_id,
                )
            await self.repository.commit()
            return StartQuestResponse(
                user_quest_id=user_quest.id,
                quest_id=quest.id,
                poi_id=user_quest.poi_id,
                status=UserQuestStatus.STARTED,
                started_at=user_quest.started_at,
            )

        try:
            created = await self.repository.create_user_quest(
                user_id=user_id,
                quest_id=quest.id,
                poi_id=poi_id,
                status=UserQuestStatus.STARTED,
                started_at=now,
            )
            if poi_id is not None:
                await self.repository.create_quest_instance_mapping(
                    user_id=user_id,
                    quest_id=quest.id,
                    poi_id=poi_id,
                )
            await self.repository.commit()
        except IntegrityError as exc:
            raise ConflictException("Quest Ä‘Ã£ Ä‘Æ°á»£c báº¯t Ä‘áº§u trÆ°á»›c Ä‘Ã³") from exc

        return StartQuestResponse(
            user_quest_id=created.id,
            quest_id=quest.id,
            poi_id=created.poi_id,
            status=UserQuestStatus.STARTED,
            started_at=created.started_at,
        )

    async def submit_quest(
        self,
        *,
        user_id: UUID,
        onboarding_completed: bool,
        quest_id: UUID,
        payload: SubmitQuestRequest,
    ) -> SubmitQuestResponse:
        if not onboarding_completed:
            raise ForbiddenException("Báº¡n cáº§n hoÃ n táº¥t onboarding trÆ°á»c khi ná»™p quest")

        quest = await self.repository.get_quest_by_id(quest_id)
        if quest is None or not quest.is_active:
            raise NotFoundException("Quest không tồn tại")

        from sqlalchemy import select
        now = datetime.now(timezone.utc)
        active_event_id = None
        if payload.is_event:
            active_event_id = await self.repository.db.scalar(
                select(Event.id)
                .join(EventQuest, EventQuest.event_id == Event.id)
                .where(
                    EventQuest.quest_id == quest.id,
                    Event.status == EventStatus.ACTIVE,
                    Event.start_at <= now,
                    Event.end_at >= now,
                )
                .order_by(Event.start_at.desc())
                .limit(1)
            )
        # Check location validity if it's an event
        is_location_valid = True
        location_fail_reason = None
        if active_event_id:
            lat = payload.lat
            lng = payload.lng
            if lat is None or lng is None:
                is_location_valid = False
                location_fail_reason = "Ảnh không chứa thông tin toạ độ (GPS)."
            else:
                active_event = await self.repository.db.scalar(
                    select(Event).where(Event.id == active_event_id)
                )
                if active_event and active_event.latitude is not None and active_event.longitude is not None and active_event.radius_m is not None:
                    from app.services.poi.poi_matcher import _haversine_m
                    dist_m = _haversine_m(lat, lng, active_event.latitude, active_event.longitude)
                    if dist_m > active_event.radius_m:
                        is_location_valid = False
                        location_fail_reason = f"Vị trí chụp ảnh cách địa điểm sự kiện {int(dist_m)}m (yêu cầu trong bán kính {int(active_event.radius_m)}m)."
                else:
                    # Fallback check Da Nang box
                    if not (15.90 <= lat <= 16.25 and 107.80 <= lng <= 108.35):
                        is_location_valid = False
                        location_fail_reason = "Bạn phải chụp ảnh tại khu vực Đà Nẵng mới được tham gia sự kiện này!"

        normalized_poi_id = None if active_event_id else (payload.poi_id if quest.location_required else None)

        if normalized_poi_id is not None:
            poi = await self.repository.get_poi_by_id(normalized_poi_id)
            if poi is None:
                raise NotFoundException("Vá»‹ trÃ­ khÃ´ng tá»“n táº¡i")

        user_quest = await self.repository.get_user_quest_for_update(
            user_id=user_id,
            quest_id=quest_id,
            poi_id=normalized_poi_id,
        )

        if user_quest is None and not quest.location_required:
            user_quest = await self.repository.get_user_quest_for_update(
                user_id=user_id,
                quest_id=quest_id,
                poi_id=None,
            )

        existing_submission = await self.repository.get_submission_by_user_quest_id(user_quest.id) if user_quest else None

        if user_quest is None:
            raise BadRequestException("Báº¡n cáº§n báº¯t Ä‘áº§u quest trÆ°á»›c khi ná»™p áº£nh")
        else:
            if (
                existing_submission is not None
                and existing_submission.status != SubmissionStatus.REJECTED
                and existing_submission.file_hash == payload.file_hash
                and user_quest.normalized_status in {UserQuestStatus.SUBMITTED, UserQuestStatus.APPROVED}
            ):
                return SubmitQuestResponse(
                    submission_id=existing_submission.id,
                    post_id=None,
                    user_quest_id=user_quest.id,
                    poi_id=user_quest.poi_id if quest.location_required else None,
                    status=user_quest.normalized_status,
                    submission_status=existing_submission.status,
                    submitted_at=existing_submission.created_at,
                    retry_count=existing_submission.retry_count,
                    max_retry_count=MAX_SUBMISSION_RETRY_COUNT,
                )

            # Náº¿u nhiá»‡m vá»¥ Ä‘Ã£ á»Ÿ tráº¡ng thÃ¡i Cuá»‘i (Ä‘Ã£ ná»™p/duyá»‡t), cháº·n khÃ´ng cho ná»™p trÃ¹ng
            if user_quest.normalized_status == UserQuestStatus.APPROVED:
                raise ConflictException("Quest Ä‘Ã£ Ä‘Æ°á»£c ná»™p hoáº·c Ä‘Ã£ hoÃ n thÃ nh trÆ°á»›c Ä‘Ã³")
            if user_quest.normalized_status == UserQuestStatus.SUBMITTED and not active_event_id:
                raise ConflictException("Quest đã được nộp trước đó")

            # Náº¿u nhiá»‡m vá»¥ Ä‘ang treo hoáº·c bá»‹ reject, tá»± Ä‘á»™ng chuyá»ƒn vá»  STARTED Ä‘á»ƒ cho phÃ©p ná»™p Ä‘Ã¨/má»›i
            if user_quest.normalized_status not in STARTED_STATUSES:
                if user_quest.normalized_status != UserQuestStatus.REJECTED and not (active_event_id and user_quest.normalized_status == UserQuestStatus.SUBMITTED):
                    raise BadRequestException("Tráº¡ng thÃ¡i quest khÃ´ng há»£p lá»‡ Ä‘á»ƒ ná»™p áº£nh")

        submission_poi_id = None if active_event_id else payload.poi_id
        poi_distance_m = None
        if submission_poi_id and payload.lat is not None and payload.lng is not None:
            from app.models.poi import Poi
            poi = await self.repository.db.scalar(select(Poi).where(Poi.id == submission_poi_id))
            if poi:
                from app.services.poi.poi_matcher import _haversine_m
                poi_distance_m = _haversine_m(payload.lat, payload.lng, poi.latitude, poi.longitude)

        if existing_submission is not None:
            if existing_submission.status == SubmissionStatus.APPROVED:
                raise ConflictException("Quest đã hoàn thành trước đó")
            if existing_submission.status != SubmissionStatus.REJECTED and not active_event_id:
                raise ConflictException("Quest Ä‘Ã£ Ä‘Æ°á»£c ná»™p trÆ°á»›c Ä‘Ã³")
            if existing_submission.status == SubmissionStatus.REJECTED and existing_submission.retry_count >= MAX_SUBMISSION_RETRY_COUNT:
                raise ConflictException("Báº¡n Ä‘Ã£ háº¿t sá»‘ láº§n cáº­p nháº­t áº£nh cho quest nÃ y")

            submission = await self.repository.update_rejected_submission_for_retry(
                existing_submission,
                image_url=payload.image_url,
                cloudinary_public_id=payload.cloudinary_public_id,
                file_hash=payload.file_hash,
                lat=payload.lat,
                lng=payload.lng,
                location_accuracy_m=payload.location_accuracy_m,
                poi_id=submission_poi_id,
                increment_retry=existing_submission.status == SubmissionStatus.REJECTED,
            )
            submission.poi_distance_m = poi_distance_m
            existing_post = await self.repository.get_post_by_submission_for_update(
                user_id=user_id,
                submission_id=submission.id,
            )
            incoming_post = None
            linked_post_id = existing_post.id if existing_post is not None else None
            if payload.post_id is not None:
                incoming_post = await self.repository.get_post_for_update(user_id=user_id, post_id=payload.post_id)
                if incoming_post is None:
                    raise NotFoundException("Post khÃƒÂ´ng tÃ¡Â»â€œn tÃ¡ÂºÂ¡i hoÃ¡ÂºÂ·c khÃƒÂ´ng thuÃ¡Â»â„¢c vÃ¡Â»Â  bÃ¡ÂºÂ¡n")
                if incoming_post.submission_id is not None and incoming_post.submission_id != submission.id:
                    raise ConflictException("Post Ã„â€˜ÃƒÂ£ gÃ¡ÂºÂ¯n vÃ¡Â»â€ºi submission khÃƒÂ¡c")
                if incoming_post.quest_id is not None and incoming_post.quest_id != quest.id:
                    raise BadRequestException("Post khÃƒÂ´ng khÃ¡Â»â€ºp vÃ¡Â»â€ºi quest Ã„â€˜ang nÃ¡Â»â„¢p")

            if existing_post is not None:
                source_post = incoming_post if incoming_post is not None and incoming_post.id != existing_post.id else None
                if source_post is not None:
                    existing_post.caption = source_post.caption
                    existing_post.location_name = source_post.location_name
                    existing_post.poi_id = source_post.poi_id or user_quest.poi_id
                elif existing_post.poi_id is None:
                    existing_post.poi_id = user_quest.poi_id if quest.location_required else None
                existing_post.image_url = payload.image_url
                existing_post.quest_id = quest.id
                existing_post.event_id = active_event_id
                if active_event_id:
                    existing_post.visibility = PostVisibility.PUBLIC
                linked_post_id = existing_post.id
                if source_post is not None:
                    await self.repository.delete_post(source_post)
            elif incoming_post is not None:
                incoming_post.submission_id = submission.id
                incoming_post.quest_id = quest.id
                incoming_post.event_id = active_event_id
                if active_event_id:
                    incoming_post.visibility = PostVisibility.PUBLIC
                incoming_post.image_url = payload.image_url
                if incoming_post.poi_id is None:
                    incoming_post.poi_id = user_quest.poi_id
                linked_post_id = incoming_post.id
            if is_location_valid:
                user_quest.status = UserQuestStatus.SUBMITTED
                await self.repository.commit()

                try:
                    enqueue_submission_approval(submission.id)
                except Exception:
                    logger.exception("Failed to enqueue AI approval for submission %s", submission.id)

                return SubmitQuestResponse(
                    submission_id=submission.id,
                    post_id=linked_post_id,
                    user_quest_id=user_quest.id,
                    poi_id=user_quest.poi_id if quest.location_required else None,
                    status=UserQuestStatus.SUBMITTED,
                    submission_status=SubmissionStatus.PENDING,
                    submitted_at=submission.created_at,
                    retry_count=submission.retry_count,
                    max_retry_count=MAX_SUBMISSION_RETRY_COUNT,
                )
            else:
                submission.status = SubmissionStatus.REJECTED
                submission.ai_metadata = {"reason": location_fail_reason}
                user_quest.status = UserQuestStatus.REJECTED
                await self.repository.commit()

                from app.services.notification.notification_service import NotificationService
                await NotificationService(self.repository.db).create_notification(
                    user_id=user_id,
                    notification_type="quest_rejected",
                    data={
                        "submission_id": str(submission.id),
                        "quest_id": str(quest.id),
                        "post_id": str(linked_post_id) if linked_post_id else None,
                        "reason": location_fail_reason,
                        "retry_count": submission.retry_count,
                        "consolation_xp": 0,
                    },
                )

                return SubmitQuestResponse(
                    submission_id=submission.id,
                    post_id=linked_post_id,
                    user_quest_id=user_quest.id,
                    poi_id=user_quest.poi_id if quest.location_required else None,
                    status=UserQuestStatus.REJECTED,
                    submission_status=SubmissionStatus.REJECTED,
                    submitted_at=submission.created_at,
                    retry_count=submission.retry_count,
                    max_retry_count=MAX_SUBMISSION_RETRY_COUNT,
                )

        try:
            submission = await self.repository.create_submission(
                user_quest_id=user_quest.id,
                image_url=payload.image_url,
                cloudinary_public_id=payload.cloudinary_public_id,
                file_hash=payload.file_hash,
                lat=payload.lat,
                lng=payload.lng,
                location_accuracy_m=payload.location_accuracy_m,
                poi_id=submission_poi_id,
            )
            submission.poi_distance_m = poi_distance_m
            if payload.post_id is not None:
                post = await self.repository.get_post_for_update(user_id=user_id, post_id=payload.post_id)
                if post is None:
                    raise NotFoundException("Post khÃ´ng tá»“n táº¡i hoáº·c khÃ´ng thuá»™c vá»  báº¡n")
                if post.submission_id is not None and post.submission_id != submission.id:
                    raise ConflictException("Post Ä‘Ã£ gáº¯n vá»›i submission khÃ¡c")
                if post.quest_id is not None and post.quest_id != quest.id:
                    raise BadRequestException("Post khÃ´ng khá»›p vá»›i quest Ä‘ang ná»™p")
                post.submission_id = submission.id
                post.quest_id = quest.id
                post.event_id = active_event_id
                if active_event_id:
                    post.visibility = PostVisibility.PUBLIC
                if post.poi_id is None:
                    post.poi_id = user_quest.poi_id if quest.location_required else None
                linked_post_id = post.id
            else:
                linked_post_id = None
            if is_location_valid:
                user_quest.status = UserQuestStatus.SUBMITTED
                await self.repository.commit()
            else:
                submission.status = SubmissionStatus.REJECTED
                submission.ai_metadata = {"reason": location_fail_reason}
                user_quest.status = UserQuestStatus.REJECTED
                await self.repository.commit()
        except IntegrityError as exc:
            raise ConflictException("Quest đã được nộp trước đó") from exc

        if is_location_valid:
            try:
                enqueue_submission_approval(submission.id)
            except Exception:
                logger.exception("Failed to enqueue AI approval for submission %s", submission.id)

            return SubmitQuestResponse(
                submission_id=submission.id,
                post_id=linked_post_id,
                user_quest_id=user_quest.id,
                poi_id=user_quest.poi_id if quest.location_required else None,
                status=UserQuestStatus.SUBMITTED,
                submission_status=SubmissionStatus.PENDING,
                submitted_at=submission.created_at,
                retry_count=submission.retry_count,
                max_retry_count=MAX_SUBMISSION_RETRY_COUNT,
            )
        else:
            from app.services.notification.notification_service import NotificationService
            await NotificationService(self.repository.db).create_notification(
                user_id=user_id,
                notification_type="quest_rejected",
                data={
                    "submission_id": str(submission.id),
                    "quest_id": str(quest.id),
                    "post_id": str(linked_post_id) if linked_post_id else None,
                    "reason": location_fail_reason,
                    "retry_count": submission.retry_count,
                    "consolation_xp": 0,
                },
            )

            return SubmitQuestResponse(
                submission_id=submission.id,
                post_id=linked_post_id,
                user_quest_id=user_quest.id,
                poi_id=user_quest.poi_id if quest.location_required else None,
                status=UserQuestStatus.REJECTED,
                submission_status=SubmissionStatus.REJECTED,
                submitted_at=submission.created_at,
                retry_count=submission.retry_count,
                max_retry_count=MAX_SUBMISSION_RETRY_COUNT,
            )

    async def recommend_from_image(
        self,
        *,
        user_id: UUID,
        image_url: str,
        lat: float | None = None,
        lng: float | None = None,
    ) -> list[QuestListItemResponse]:
        """Uses Google Vision to detect what's in the image and recommends quests matching it."""
        try:
            vision_service = VisionService()
            result = vision_service.detect_labels_from_url(image_url)
            detected_labels = {label.description.lower() for label in result.labels}
        except Exception:
            logger.warning("AI label detection failed for recommendations. Defaulting to zero filter.")
            detected_labels = set()

        if not detected_labels:
            return []

        # Fetch reasonable number of active candidates to check (e.g. top 200 recent)
        quests, _ = await self.repository.list_active_quests(offset=0, limit=200)
        matched_items: list[QuestListItemResponse] = []

        for quest in quests:


            # Combine labels from list and key mapping logic exactly like runtime evaluator
            quest_targets = set(quest.labels or [])
            if quest.label_rules:
                quest_targets.update(quest.label_rules.keys())
            
            quest_targets_lower = {t.lower() for t in quest_targets}
            
            # Check if ANY label intersects with detected image labels
            if any(l in detected_labels for l in quest_targets_lower):
                user_quest = await self.repository.get_user_quest(user_id=user_id, quest_id=quest.id)
                # Loáº¡i trá»« cÃ¡c nhiá»‡m vá»¥ Ä‘Ã£ lÃ m rá»“i theo yÃªu cáº§u cá»§a ngÆ°á»i dÃ¹ng
                if user_quest and user_quest.normalized_status in {UserQuestStatus.APPROVED, UserQuestStatus.SUBMITTED}:
                    continue
                
                matched_items.append(


                    QuestListItemResponse(
                        id=quest.id,
                        poi_id=None,
                        rendered_text=render_quest_text(quest.template, quest.labels, None),
                        labels=quest.labels or [],
                        min_confidence=float(quest.min_confidence or 0.5),
                        xp_reward=quest.xp_reward,
                        is_active=quest.is_active,
                        image_url=quest.image_url,
                        user_status=user_quest.normalized_status if user_quest else UserQuestStatus.NOT_STARTED,
                    )
                )
        
        return matched_items
