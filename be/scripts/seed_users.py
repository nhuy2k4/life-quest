import argparse
import asyncio
import logging
import random
import sys
from pathlib import Path
from typing import Iterable, TypedDict

from faker import Faker
from sqlalchemy import insert, select

# Ensure project root is on sys.path when running as a script.
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.enums import AuthProvider, UserRole
from app.models.user import User


DEFAULT_TOTAL = 50
DEFAULT_BATCH_SIZE = 25
DEFAULT_PASSWORD = "123456"
MAX_ATTEMPTS_FACTOR = 10

logger = logging.getLogger("seed_users")


class UserInsertRow(TypedDict, total=False):
    username: str
    display_name: str | None
    email: str
    password_hash: str
    bio: str | None
    xp: int
    streak_days: int
    trust_score: float
    onboarding_completed: bool
    role: UserRole
    is_verified: bool
    level_id: int
    provider: AuthProvider
    provider_id: str | None
    avatar_url: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed normal users for testing.")
    parser.add_argument("--total", type=int, default=DEFAULT_TOTAL, help="Number of users to insert.")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Commit batch size.")
    parser.add_argument("--seed", type=int, default=None, help="Optional random seed for reproducibility.")
    return parser.parse_args()


def chunked(items: list[UserInsertRow], size: int) -> Iterable[list[UserInsertRow]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def truncate(value: str, max_len: int) -> str:
    if len(value) <= max_len:
        return value
    return value[:max_len]


def random_avatar_url(rng: random.Random) -> str:
    gender = "men" if rng.random() < 0.5 else "women"
    img_id = rng.randint(1, 99)
    return f"https://randomuser.me/api/portraits/{gender}/{img_id}.jpg"


def generate_xp(rng: random.Random) -> tuple[int, str]:
    segment = rng.choices(
        ["active", "newbie", "hardcore"],
        weights=[0.6, 0.3, 0.1],
        k=1,
    )[0]
    if segment == "newbie":
        return rng.randint(0, 200), segment
    if segment == "hardcore":
        return rng.randint(3000, 10000), segment
    return rng.randint(200, 3000), segment


def generate_streak_days(rng: random.Random, segment: str) -> int:
    if segment == "newbie":
        return rng.randint(0, 3)
    if segment == "hardcore":
        return rng.randint(10, 120)
    return rng.randint(3, 30)


def generate_trust_score(rng: random.Random, segment: str) -> float:
    if segment == "newbie":
        return round(rng.uniform(0.9, 1.1), 2)
    if segment == "hardcore":
        return round(rng.uniform(1.2, 2.0), 2)
    return round(rng.uniform(1.0, 1.5), 2)


def generate_username(faker: Faker, rng: random.Random, existing: set[str]) -> str:
    base = truncate(faker.user_name().lower(), 30)
    candidate = base
    while candidate in existing:
        suffix = rng.randint(100, 9999)
        candidate = truncate(f"{base}{suffix}", 50)
    return candidate


def generate_email(faker: Faker, rng: random.Random, existing: set[str], username: str) -> str:
    domain = faker.free_email_domain()
    candidate = f"{username}@{domain}".lower()
    while candidate in existing:
        suffix = rng.randint(100, 9999)
        candidate = f"{username}{suffix}@{domain}".lower()
    return candidate


def build_user_row(
    faker: Faker,
    rng: random.Random,
    existing_usernames: set[str],
    existing_emails: set[str],
    password_hash: str,
) -> UserInsertRow:
    username = generate_username(faker, rng, existing_usernames)
    email = generate_email(faker, rng, existing_emails, username)
    xp, segment = generate_xp(rng)

    row: UserInsertRow = {
        "username": username,
        "display_name": truncate(faker.name(), 80),
        "email": email,
        "password_hash": password_hash,
        "bio": truncate(faker.sentence(nb_words=12), 150),
        "xp": xp,
        "streak_days": generate_streak_days(rng, segment),
        "trust_score": generate_trust_score(rng, segment),
        "onboarding_completed": True,
        "role": UserRole.USER,
        "is_verified": True,
        "level_id": 1,
        "provider": AuthProvider.LOCAL,
        "provider_id": None,
    }

    if hasattr(User, "avatar_url"):
        row["avatar_url"] = random_avatar_url(rng)

    return row


async def fetch_existing_identities() -> tuple[set[str], set[str]]:
    async with AsyncSessionLocal() as session:
        rows = await session.execute(select(User.username, User.email))
        existing_usernames: set[str] = set()
        existing_emails: set[str] = set()
        for username, email in rows.all():
            if username:
                existing_usernames.add(username.lower())
            if email:
                existing_emails.add(email.lower())
        return existing_usernames, existing_emails


async def seed_users(total: int, batch_size: int, seed: int | None) -> int:
    faker = Faker("en_US")
    rng = random.Random(seed)

    existing_usernames, existing_emails = await fetch_existing_identities()
    password_hash = hash_password(DEFAULT_PASSWORD)

    candidates: list[UserInsertRow] = []
    attempts = 0
    max_attempts = max(total * MAX_ATTEMPTS_FACTOR, total + 10)

    while len(candidates) < total and attempts < max_attempts:
        attempts += 1
        row = build_user_row(faker, rng, existing_usernames, existing_emails, password_hash)
        existing_usernames.add(row["username"].lower())
        existing_emails.add(row["email"].lower())
        candidates.append(row)

    if len(candidates) < total:
        logger.warning("Only generated %d/%d users after %d attempts.", len(candidates), total, attempts)

    inserted = 0
    async with AsyncSessionLocal() as session:
        for batch in chunked(candidates, batch_size):
            try:
                async with session.begin():
                    await session.execute(insert(User), batch)
                inserted += len(batch)
            except Exception:
                await session.rollback()
                logger.exception("Failed to seed a batch. Rolling back.")
                raise

    return inserted


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    args = parse_args()
    inserted = asyncio.run(seed_users(args.total, args.batch_size, args.seed))
    print(f"[OK] Seeded {inserted} users successfully")


if __name__ == "__main__":
    main()
