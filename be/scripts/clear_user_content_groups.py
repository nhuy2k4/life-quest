import argparse
import asyncio
import sys
from pathlib import Path

# Ensure project root is on sys.path when running as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.core.database import engine


DEFAULT_TABLES = [
	"recommendation_logs",
	"ai_detection_logs",
	"audit_logs",
	"comments",
	"likes",
	"posts",
	"submissions",
	"user_badges",
	"user_quests",
]


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Clear only user content groups: posts, achievements, and quest progress.")
	parser.add_argument(
		"--tables",
		nargs="*",
		default=DEFAULT_TABLES,
		help="Optional explicit table list to truncate. Defaults to the three user-content groups and their direct dependents.",
	)
	parser.add_argument(
		"--apply",
		action="store_true",
		help="Actually execute the TRUNCATE. Without this flag the script only prints the SQL it would run.",
	)
	return parser.parse_args()


def build_truncate_sql(tables: list[str]) -> str:
	return f"TRUNCATE TABLE {', '.join(tables)} RESTART IDENTITY CASCADE;"


async def apply_truncate(tables: list[str]) -> None:
	query = build_truncate_sql(tables)
	async with engine.begin() as conn:
		await conn.execute(text(query))


async def main_async() -> int:
	args = parse_args()
	query = build_truncate_sql(args.tables)

	print("--- User content cleanup plan ---")
	print(query)

	if not args.apply:
		print("[DRY-RUN] Nothing was deleted. Re-run with --apply to execute.")
		return 0

	await apply_truncate(args.tables)
	print("[OK] Cleared user posts, achievements, quest progress, and direct dependent logs.")
	return 0


def main() -> None:
	raise SystemExit(asyncio.run(main_async()))


if __name__ == "__main__":
	main()