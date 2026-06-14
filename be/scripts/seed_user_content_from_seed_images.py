import argparse
import asyncio
import json
import random
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ensure project root is on sys.path when running as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete, select

from app.core.database import AsyncSessionLocal
from app.models.enums import SubmissionStatus, UserQuestStatus, UserRole
from app.models.quest import Quest
from app.models.social import Post
from app.models.submission import Submission
from app.models.user import User
from app.models.user_quest import UserQuest


CONFIG_PATH = Path(__file__).with_name("quest_image_folder_mapping.json")
IMAGE_ROOT = Path(__file__).resolve().parent.parent / "seed-images"
DEFAULT_BASE_URL = "/seed-images"
ALLOWED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass(frozen=True)
class SeedImageItem:
	folder: str
	file_path: Path
	image_url: str
	folder_labels: set[str]


@dataclass(frozen=True)
class PlannedContent:
	image: SeedImageItem
	user_id: uuid.UUID
	quest_id: uuid.UUID
	quest_title: str
	caption: str
	location_name: str | None
	post_id: uuid.UUID
	user_quest_id: uuid.UUID
	submission_id: uuid.UUID


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Seed posts, submissions, and quest progress from seed image folders.")
	parser.add_argument("--config", type=Path, default=CONFIG_PATH, help="Path to the Vision-label folder mapping JSON.")
	parser.add_argument("--image-root", type=Path, default=IMAGE_ROOT, help="Root folder that contains the image directories.")
	parser.add_argument("--base-url", type=str, default=DEFAULT_BASE_URL, help="Base URL/path prefix stored in image_url fields.")
	parser.add_argument("--seed", type=int, default=None, help="Optional random seed for reproducibility.")
	parser.add_argument("--apply", action="store_true", help="Persist the generated records. Without this flag the script only prints the plan.")
	parser.add_argument("--clear-existing", action="store_true", help="Delete existing seeded posts/submissions/user_quests before inserting new ones.")
	return parser.parse_args()


def normalize_label(value: str) -> str:
	return " ".join(value.strip().lower().replace("_", " ").replace("-", " ").split())


def normalize_labels(values: list[str] | tuple[str, ...] | None) -> set[str]:
	if not values:
		return set()
	return {normalize_label(str(value)) for value in values if str(value).strip()}


def load_config(path: Path) -> dict:
	with path.open("r", encoding="utf-8") as handle:
		return json.load(handle)


def collect_seed_images(image_root: Path, folder_vision_labels: dict[str, list[str]], base_url: str) -> list[SeedImageItem]:
	items: list[SeedImageItem] = []
	base_url = base_url.rstrip("/")
	for folder_path in sorted(image_root.iterdir()):
		if not folder_path.is_dir():
			continue
		folder = folder_path.name
		labels = normalize_labels(folder_vision_labels.get(folder, []))
		for file_path in sorted(folder_path.iterdir()):
			if not file_path.is_file() or file_path.suffix.lower() not in ALLOWED_IMAGE_SUFFIXES:
				continue
			image_url = f"{base_url}/{folder}/{file_path.name}" if base_url else f"/{folder}/{file_path.name}"
			items.append(SeedImageItem(folder=folder, file_path=file_path, image_url=image_url, folder_labels=labels))
	return items


async def fetch_existing_users() -> list[User]:
	async with AsyncSessionLocal() as session:
		rows = await session.scalars(
			select(User)
			.where(User.role == UserRole.USER)
			.order_by(User.created_at.asc())
		)
		return list(rows.all())


async def fetch_quests() -> list[Quest]:
	async with AsyncSessionLocal() as session:
		rows = await session.scalars(select(Quest).where(Quest.is_active.is_(True)).order_by(Quest.created_at.asc()))
		return list(rows.all())


async def clear_existing_content() -> None:
	async with AsyncSessionLocal() as session:
		await session.execute(delete(Post).where(Post.submission_id.is_not(None)))
		await session.execute(delete(Submission))
		await session.execute(delete(UserQuest))
		await session.commit()


def compute_quest_weights_for_folder(
	folder: str,
	folder_labels: set[str],
	quests: list[Quest],
	quest_folder_weights: dict[str, dict[str, float]],
	quest_title_aliases: dict[str, set[str]],
	) -> list[tuple[Quest, float]]:
	candidates: list[tuple[Quest, float]] = []
	for quest in quests:
		quest_targets = normalize_labels(quest.labels or [])
		if quest.label_rules:
			quest_targets |= {normalize_label(key) for key in quest.label_rules.keys()}
		title_aliases = quest_title_aliases.get(quest.title, set())
		quest_targets |= title_aliases
		overlap = folder_labels & quest_targets
		manual_weight = quest_folder_weights.get(quest.title, {}).get(folder, 0.0)
		if manual_weight <= 0 and not overlap:
			continue
		weight = manual_weight if manual_weight > 0 else float(len(overlap))
		if weight > 0:
			candidates.append((quest, weight))
	return candidates


def weighted_choice(rng: random.Random, items: list[tuple[Quest, float]]) -> Quest | None:
	if not items:
		return None
	quests = [quest for quest, _ in items]
	weights = [weight for _, weight in items]
	return rng.choices(quests, weights=weights, k=1)[0]


def build_plan(
	images: list[SeedImageItem],
	users: list[User],
	quests: list[Quest],
	quest_folder_weights: dict[str, dict[str, float]],
	quest_title_aliases: dict[str, set[str]],
	rng: random.Random,
	) -> list[PlannedContent]:
	plan: list[PlannedContent] = []
	if not users or not quests:
		return plan

	user_cycle = iter(users)
	for index, image in enumerate(images):
		try:
			user = next(user_cycle)
		except StopIteration:
			user_cycle = iter(users)
			user = next(user_cycle)

		candidates = compute_quest_weights_for_folder(
			image.folder,
			image.folder_labels,
			quests,
			quest_folder_weights,
			quest_title_aliases,
		)
		quest = weighted_choice(rng, candidates)
		if quest is None:
			continue

		content_seed = f"{image.folder}:{image.file_path.stem}:{index}"
		caption = f"Seeded post from {image.folder} image {image.file_path.stem}"
		location_name = image.folder.title()
		plan.append(
			PlannedContent(
				image=image,
				user_id=user.id,
				quest_id=quest.id,
				quest_title=quest.title,
				caption=caption,
				location_name=location_name,
				post_id=uuid.uuid5(uuid.NAMESPACE_URL, f"lifequest-post:{content_seed}"),
				user_quest_id=uuid.uuid5(uuid.NAMESPACE_URL, f"lifequest-userquest:{content_seed}"),
				submission_id=uuid.uuid5(uuid.NAMESPACE_URL, f"lifequest-submission:{content_seed}"),
			)
		)

	return plan


def plan_to_json(plan: list[PlannedContent]) -> list[dict]:
	return [
		{
			"folder": item.image.folder,
			"file": item.image.file_path.name,
			"image_url": item.image.image_url,
			"user_id": str(item.user_id),
			"quest_id": str(item.quest_id),
			"quest_title": item.quest_title,
			"post_id": str(item.post_id),
			"user_quest_id": str(item.user_quest_id),
			"submission_id": str(item.submission_id),
			"caption": item.caption,
			"location_name": item.location_name,
		}
		for item in plan
	]


async def apply_plan(plan: list[PlannedContent]) -> None:
	if not plan:
		return

	now = datetime.now(timezone.utc)
	async with AsyncSessionLocal() as session:
		for item in plan:
			user_quest = UserQuest(
				id=item.user_quest_id,
				user_id=item.user_id,
				quest_id=item.quest_id,
				poi_id=None,
				status=UserQuestStatus.APPROVED,
				started_at=now - timedelta(hours=2),
				consolation_xp=0,
			)
			submission = Submission(
				id=item.submission_id,
				user_quest_id=item.user_quest_id,
				image_url=item.image.image_url,
				cloudinary_public_id=f"seed/{item.image.folder}/{item.image.file_path.stem}",
				file_hash=str(uuid.uuid5(uuid.NAMESPACE_URL, f"lifequest-filehash:{item.image.file_path.as_posix()}")),
				retry_count=0,
				vision_labels=[{"label": label, "score": 0.95} for label in sorted(item.image.folder_labels)] or None,
				vision_raw={"seed_folder": item.image.folder, "seed_file": item.image.file_path.name},
				lat=None,
				lng=None,
				location_accuracy_m=None,
				poi_id=None,
				poi_distance_m=None,
				cheat_flags=None,
				ai_score=0.99,
				status=SubmissionStatus.APPROVED,
				is_suspicious=False,
			)
			post = Post(
				id=item.post_id,
				user_id=item.user_id,
				submission_id=item.submission_id,
				quest_id=item.quest_id,
				poi_id=None,
				event_id=None,
				like_count=0,
				comment_count=0,
				image_url=item.image.image_url,
				caption=item.caption,
				location_name=item.location_name,
			)
			session.add_all([user_quest, submission, post])
			await session.flush()
		await session.commit()


async def main_async() -> int:
	args = parse_args()
	config = load_config(args.config)
	folder_vision_labels: dict[str, list[str]] = config.get("folder_vision_labels", {})
	quest_folder_weights: dict[str, dict[str, float]] = config.get("quest_folder_weights", {})
	quest_title_aliases: dict[str, set[str]] = {
		"Drinkware shot": {"drinkware", "cup", "water bottle", "drink", "beverage"},
		"Coffee hunt": {"coffee", "cup", "mug", "drink", "beverage"},
		"Drink moment": {"drink", "beverage"},
		"Laptop shot": {"laptop", "computer", "personal computer"},
		"Bag shot": {"bag", "backpack", "handbag"},
		"People shot": {"person", "people", "human"},
		"Dog shot": {"dog", "puppy", "pet"},
		"Cat shot": {"cat", "kitten", "pet"},
		"Bridge view": {"bridge"},
	}
	rng = random.Random(args.seed)

	users = await fetch_existing_users()
	quests = await fetch_quests()
	images = collect_seed_images(args.image_root, folder_vision_labels, args.base_url)

	if args.clear_existing:
		await clear_existing_content()

	plan = build_plan(
		images=images,
		users=users,
		quests=quests,
		quest_folder_weights=quest_folder_weights,
		quest_title_aliases=quest_title_aliases,
		rng=rng,
	)
	plan_json = plan_to_json(plan)

	print(json.dumps(plan_json, ensure_ascii=False, indent=2))
	print(f"[PLAN] images={len(images)} users={len(users)} generated_records={len(plan)}")

	if not args.apply:
		print("[DRY-RUN] Database not modified. Re-run with --apply to persist the generated records.")
		return 0

	await apply_plan(plan)
	print(f"[OK] Seeded {len(plan)} submissions/posts/user_quests across {len(users)} users")
	return 0


def main() -> None:
	raise SystemExit(asyncio.run(main_async()))


if __name__ == "__main__":
	main()