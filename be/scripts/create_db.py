"""
Script: create_db.py
Mục đích: Tự động tạo database 'lifequest' nếu chưa tồn tại.
Dùng asyncpg trực tiếp để connect vào postgres (system DB) và CREATE DATABASE.

Chạy: python scripts/create_db.py
"""
import asyncio
import os
import sys
from pathlib import Path

# Thêm project root vào sys.path để import được app.core.config
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg
from app.core.config import settings


def _parse_db_url(url: str) -> dict:
    """Parse DATABASE_URL thành các thành phần."""
    # Bỏ driver prefix
    url = url.replace("postgresql+asyncpg://", "").replace("postgresql://", "")
    # user:password@host:port/dbname
    user_pass, rest = url.split("@", 1)
    host_port, dbname = rest.rsplit("/", 1)
    user, password = user_pass.split(":", 1)
    if ":" in host_port:
        host, port = host_port.rsplit(":", 1)
    else:
        host, port = host_port, "5432"
    return {
        "user": user,
        "password": password,
        "host": host,
        "port": int(port),
        "database": dbname,
    }


async def create_database_if_not_exists():
    params = _parse_db_url(settings.DATABASE_URL)
    target_db = params["database"]

    print(f"[create_db] Connecting to postgres@{params['host']}:{params['port']} ...")

    # Connect vào DB mặc định 'postgres' (luôn tồn tại)
    conn = await asyncpg.connect(
        user=params["user"],
        password=params["password"],
        host=params["host"],
        port=params["port"],
        database="postgres",  # system DB, luôn tồn tại
    )

    try:
        # Kiểm tra database đã tồn tại chưa
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", target_db
        )
        if exists:
            print(f"[create_db] ✅ Database '{target_db}' đã tồn tại.")
        else:
            # CREATE DATABASE không dùng được trong transaction → dùng execute trực tiếp
            await conn.execute(f'CREATE DATABASE "{target_db}"')
            print(f"[create_db] ✅ Đã tạo database '{target_db}' thành công!")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(create_database_if_not_exists())
