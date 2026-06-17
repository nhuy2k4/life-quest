import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.poi import Poi

async def main():
    async with AsyncSessionLocal() as session:
        pois = (await session.scalars(select(Poi))).all()
        print(f"\nTotal POIs in database: {len(pois)}")
        for p in pois:
            print(f"POI: {p.name} (ID: {p.id}, type: {p.poi_type}, active: {p.is_active})")
            print(f"  lat, lng: {p.latitude}, {p.longitude}")
            print(f"  radius_m: {p.radius_m}")
            print("-" * 40)

if __name__ == "__main__":
    asyncio.run(main())
