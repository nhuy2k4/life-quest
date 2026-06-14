import argparse
import asyncio
import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path

# Ensure project root is on sys.path when running as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, update

from app.core.database import AsyncSessionLocal
from app.models.quest import Quest


CONFIG_PATH = Path(__file__).with_name("quest_image_folder_mapping.json")
IMAGE_ROOT = Path(__file__).resolve().parent.parent / "seed-images"
DEFAULT_BASE_URL = "/seed-images"
ALLOWED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass(frozen=True)
class QuestImageChoice:
	quest_id: str
	quest_title: str
	selected_folder: str | None
	selected_file: str | None
	selected_url: str | None
	candidate_weights: dict[str, float]
	reason: str


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Seed quest.image_url from folder-level Vision AI labels.")
	parser.add_argument("--config", type=Path, default=CONFIG_PATH, help="Path to the mapping JSON file.")
	parser.add_argument("--image-root", type=Path, default=IMAGE_ROOT, help="Root folder containing seed image directories.")
	parser.add_argument("--base-url", type=str, default=DEFAULT_BASE_URL, help="Base URL/path prefix stored in quest.image_url.")
	parser.add_argument("--seed", type=int, default=None, help="Optional random seed for reproducible selection.")
	parser.add_argument("--output", type=Path, default=None, help="Optional JSON file to write the resolved plan to.")
	parser.add_argument("--apply", action="store_true", help="Persist quest.image_url updates to the database.")
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


def collect_images(folder_path: Path) -> list[Path]:
	if not folder_path.exists() or not folder_path.is_dir():
		return []
	images = [
		path
		for path in sorted(folder_path.iterdir())
		if path.is_file() and path.suffix.lower() in ALLOWED_IMAGE_SUFFIXES
	]
	return images


def compute_candidate_weights(
	quest_labels: set[str],
	folder_vision_labels: dict[str, list[str]],
	manual_weights: dict[str, float] | None,
) -> dict[str, float]:
	candidate_weights: dict[str, float] = {}
	manual_weights = manual_weights or {}

	for folder_name, folder_labels in folder_vision_labels.items():
		folder_label_set = normalize_labels(folder_labels)
		overlap = quest_labels & folder_label_set
		if not overlap:
			continue

		weight = float(manual_weights.get(folder_name, len(overlap)))
		if weight > 0:
			candidate_weights[folder_name] = weight

	return candidate_weights


def weighted_choice(rng: random.Random, items: dict[str, float]) -> str | None:
	if not items:
		return None
	names = list(items.keys())
	weights = list(items.values())
	return rng.choices(names, weights=weights, k=1)[0]


async def fetch_quests() -> list[Quest]:
	async with AsyncSessionLocal() as session:
		result = await session.scalars(select(Quest).order_by(Quest.created_at.asc()))
		return list(result.all())


async def apply_updates(plan: list[QuestImageChoice]) -> int:
	updated = 0
	async with AsyncSessionLocal() as session:
		for item in plan:
			if not item.selected_url:
				continue
			await session.execute(
				update(Quest)
				.where(Quest.id == item.quest_id)
				.values(image_url=item.selected_url)
			)
			updated += 1
		await session.commit()
	return updated


async def build_plan(args: argparse.Namespace) -> list[QuestImageChoice]:
	config = load_config(args.config)
	folder_vision_labels: dict[str, list[str]] = config.get("folder_vision_labels", {})
	manual_quest_weights: dict[str, dict[str, float]] = config.get("quest_folder_weights", {})
	quests = await fetch_quests()
	rng = random.Random(args.seed)
	plan: list[QuestImageChoice] = []

	for quest in quests:
		quest_labels = normalize_labels(quest.labels or [])
		manual_weights = manual_quest_weights.get(quest.title, {})
		candidate_weights = compute_candidate_weights(quest_labels, folder_vision_labels, manual_weights)

		selected_folder = weighted_choice(rng, candidate_weights)
		if selected_folder is None:
			plan.append(
				QuestImageChoice(
					quest_id=str(quest.id),
					quest_title=quest.title,
					selected_folder=None,
					selected_file=None,
					selected_url=None,
					candidate_weights=candidate_weights,
					reason="no high-relevance folder match",
				)
			)
			continue

		folder_path = args.image_root / selected_folder
		images = collect_images(folder_path)
		if not images:
			plan.append(
				QuestImageChoice(
					quest_id=str(quest.id),
					quest_title=quest.title,
					selected_folder=selected_folder,
					selected_file=None,
					selected_url=None,
					candidate_weights=candidate_weights,
					reason="matched folder has no image files",
				)
			)
			continue

		selected_file = rng.choice(images)
		base_url = args.base_url.rstrip("/")
		selected_url = f"{base_url}/{selected_folder}/{selected_file.name}" if base_url else f"{selected_folder}/{selected_file.name}"
		plan.append(
			QuestImageChoice(
				quest_id=str(quest.id),
				quest_title=quest.title,
				selected_folder=selected_folder,
				selected_file=selected_file.name,
				selected_url=selected_url,
				candidate_weights=candidate_weights,
				reason="selected from high-relevance folder pool",
			)
		)

	return plan


def plan_to_json(plan: list[QuestImageChoice]) -> dict:
	resolved = {}
	for item in plan:
		resolved[item.quest_title] = {
			"quest_id": item.quest_id,
			"selected_folder": item.selected_folder,
			"selected_file": item.selected_file,
			"image_url": item.selected_url,
			"candidate_weights": item.candidate_weights,
			"reason": item.reason,
		}
	return resolved


async def main_async() -> int:
	args = parse_args()
	plan = await build_plan(args)
	plan_json = plan_to_json(plan)

	print(json.dumps(plan_json, ensure_ascii=False, indent=2))

	if args.output is not None:
		args.output.parent.mkdir(parents=True, exist_ok=True)
		with args.output.open("w", encoding="utf-8") as handle:
			json.dump(plan_json, handle, ensure_ascii=False, indent=2)
			handle.write("\n")

	if args.apply:
		updated = await apply_updates(plan)
		print(f"[OK] Updated {updated} quests")
	else:
		print("[DRY-RUN] Database not modified. Re-run with --apply to persist quest.image_url.")

	return 0


def main() -> None:
	raise SystemExit(asyncio.run(main_async()))


if __name__ == "__main__":
	main()