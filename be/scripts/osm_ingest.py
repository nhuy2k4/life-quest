from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from typing import Any, Iterable

SCRIPT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

import requests
from sqlalchemy import func, literal_column
from sqlalchemy.dialects.postgresql import insert

from app.core.database import AsyncSessionLocal
from app.models.poi import Poi

OSM_TAG_MAP: dict[tuple[str, str], str] = {
    ("amenity", "cafe"): "cafe",
    ("amenity", "restaurant"): "restaurant",
    ("leisure", "park"): "park",
    ("shop", "mall"): "mall",
}

DEFAULT_RADIUS_M: dict[str, float] = {
    "cafe": 40.0,
    "restaurant": 50.0,
    "park": 200.0,
    "mall": 120.0,
}

TAG_PRIORITY = ["amenity", "leisure", "shop"]

REQUIRED_UNIQUE_INDEX = (
    "CREATE UNIQUE INDEX uq_pois_source_external_id ON pois (source, external_id);"
)


def build_overpass_query(*, south: float, west: float, north: float, east: float) -> str:
    tag_filters = [
        "node[amenity=cafe]({s},{w},{n},{e});".format(s=south, w=west, n=north, e=east),
        "node[amenity=restaurant]({s},{w},{n},{e});".format(s=south, w=west, n=north, e=east),
        "node[leisure=park]({s},{w},{n},{e});".format(s=south, w=west, n=north, e=east),
        "node[shop=mall]({s},{w},{n},{e});".format(s=south, w=west, n=north, e=east),
        "way[amenity=cafe]({s},{w},{n},{e});".format(s=south, w=west, n=north, e=east),
        "way[amenity=restaurant]({s},{w},{n},{e});".format(s=south, w=west, n=north, e=east),
        "way[leisure=park]({s},{w},{n},{e});".format(s=south, w=west, n=north, e=east),
        "way[shop=mall]({s},{w},{n},{e});".format(s=south, w=west, n=north, e=east),
    ]
    return "[out:json];({filters});out center;".format(filters="".join(tag_filters))


def fetch_osm_data(*, url: str, query: str) -> list[dict[str, Any]]:
    response = requests.post(url, data={"data": query}, timeout=30)
    response.raise_for_status()
    payload = response.json()
    return payload.get("elements", [])


def normalize_poi(osm_item: dict[str, Any]) -> dict[str, Any] | None:
    tags = osm_item.get("tags", {})
    for key in TAG_PRIORITY:
        value = tags.get(key)
        if value is None:
            continue
        poi_type = OSM_TAG_MAP.get((key, value))
        if poi_type is None:
            continue
        name = tags.get("name") or poi_type.title()
        lat = osm_item.get("lat") or (osm_item.get("center") or {}).get("lat")
        lng = osm_item.get("lon") or (osm_item.get("center") or {}).get("lon")
        if lat is None or lng is None:
            return None
        return {
            "name": name,
            "poi_type": poi_type,
            "latitude": float(lat),
            "longitude": float(lng),
            "radius_m": DEFAULT_RADIUS_M[poi_type],
            "source": "osm",
            "external_id": str(osm_item.get("id")),
            "external_type": str(osm_item.get("type")) if osm_item.get("type") else None,
            "is_active": True,
        }
    return None


def chunk_data(items: Iterable[dict[str, Any]], size: int) -> Iterable[list[dict[str, Any]]]:
    batch: list[dict[str, Any]] = []
    for item in items:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


async def upsert_pois(pois: list[dict[str, Any]], *, batch_size: int) -> tuple[int, int]:
    if not pois:
        return 0, 0

    inserted = 0
    updated = 0

    async with AsyncSessionLocal() as session:
        for batch in chunk_data(pois, batch_size):
            if not batch:
                continue

            stmt = insert(Poi).values(batch)
            stmt = stmt.on_conflict_do_update(
                index_elements=[Poi.source, Poi.external_id],
                set_={
                    "name": stmt.excluded.name,
                    "poi_type": stmt.excluded.poi_type,
                    "latitude": stmt.excluded.latitude,
                    "longitude": stmt.excluded.longitude,
                    "radius_m": stmt.excluded.radius_m,
                    "external_type": stmt.excluded.external_type,
                    "is_active": stmt.excluded.is_active,
                    "updated_at": func.now(),
                },
            )

            result = await session.execute(
                stmt.returning(literal_column("xmax = 0").label("inserted"))
            )
            await session.commit()

            rows = result.fetchall()
            inserted_rows = sum(1 for row in rows if row.inserted)
            inserted += inserted_rows
            updated += len(rows) - inserted_rows

    return inserted, updated


async def run_ingest(args: argparse.Namespace) -> None:
    query = build_overpass_query(
        south=args.south,
        west=args.west,
        north=args.north,
        east=args.east,
    )
    if args.print_query:
        print("====== OSM QUERY ======")
        print(query)
        print("=======================")

    elements = fetch_osm_data(url=args.overpass_url, query=query)

    mapped: list[dict[str, Any]] = []
    for element in elements:
        poi = normalize_poi(element)
        if poi:
            mapped.append(poi)

    if args.dump_json:
        print(json.dumps(mapped[: args.dump_limit], ensure_ascii=True, indent=2))

    inserted, updated = await upsert_pois(mapped, batch_size=args.batch_size)
    print(f"Inserted: {inserted}")
    print(f"Updated: {updated}")
    print(f"Total processed: {len(mapped)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest OSM POIs into the database.")
    parser.add_argument("--south", type=float, required=True)
    parser.add_argument("--west", type=float, required=True)
    parser.add_argument("--north", type=float, required=True)
    parser.add_argument("--east", type=float, required=True)
    parser.add_argument("--overpass-url", default="https://overpass-api.de/api/interpreter")
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--dump-json", action="store_true")
    parser.add_argument("--dump-limit", type=int, default=10)
    parser.add_argument("--print-query", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(run_ingest(args))


if __name__ == "__main__":
    main()
