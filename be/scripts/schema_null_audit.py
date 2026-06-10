import asyncio
import json
import os
from pathlib import Path

import asyncpg
from dotenv import dotenv_values


def get_database_url() -> str:
    backend_root = Path(__file__).resolve().parents[1]
    env_values = dotenv_values(backend_root / ".env")
    url = os.getenv("DATABASE_URL") or env_values.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL was not found in environment or be/.env")
    return url.replace("postgresql+asyncpg://", "postgresql://")


async def main() -> None:
    url = get_database_url()
    conn = await asyncpg.connect(url)
    try:
        tables = await conn.fetch(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
              AND table_name != 'alembic_version'
            ORDER BY table_name
            """
        )

        report = []
        for table_row in tables:
            table_name = table_row["table_name"]
            columns = await conn.fetch(
                """
                SELECT column_name, is_nullable, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = $1
                ORDER BY ordinal_position
                """,
                table_name,
            )
            quoted_table = '"' + table_name.replace('"', '""') + '"'
            count_parts = []
            for column in columns:
                column_name = column["column_name"]
                quoted_column = '"' + column_name.replace('"', '""') + '"'
                count_parts.append(f'COUNT({quoted_column}) AS {quoted_column}')

            row = await conn.fetchrow(
                f"SELECT COUNT(*) AS total, {', '.join(count_parts)} FROM {quoted_table}"
            )
            total = row["total"]
            all_null_columns = []
            partial_null_columns = []

            for column in columns:
                column_name = column["column_name"]
                non_null = row[column_name]
                if total > 0 and non_null == 0:
                    all_null_columns.append(
                        {
                            "column": column_name,
                            "type": column["data_type"],
                            "nullable": column["is_nullable"],
                        }
                    )
                elif total > 0 and non_null < total:
                    partial_null_columns.append(
                        {
                            "column": column_name,
                            "non_null": non_null,
                            "total": total,
                            "nulls": total - non_null,
                        }
                    )

            report.append(
                {
                    "table": table_name,
                    "rows": total,
                    "columns": len(columns),
                    "all_null_columns": all_null_columns,
                    "partial_null_columns": partial_null_columns,
                }
            )

        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
