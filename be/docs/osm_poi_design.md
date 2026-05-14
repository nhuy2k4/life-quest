# OSM Integration Design (POI Ingestion + Mapping)

## 1) Scope and goals

- Use OSM as primary POI source.
- Store normalized POIs only (no raw OSM payloads in production tables).
- Support manual POIs and user-suggested POIs.
- Efficient lookup by lat/lng or geospatial index.

---

## 2) POI schema (production-ready)

### `pois`

- `id` (uuid, pk)
- `name` (varchar, not null)
- `poi_type` (varchar, not null) # normalized: cafe, restaurant, park, mall
- `latitude` (double precision, not null)
- `longitude` (double precision, not null)
- `radius_m` (float, not null)
- `source` (varchar, not null) # osm | manual | user
- `external_id` (varchar, nullable) # OSM node/way id
- `external_type` (varchar, nullable) # node | way | relation (optional)
- `is_active` (bool, not null, default true)
- `created_at` (timestamp, not null)
- `updated_at` (timestamp, not null)

**Notes**

- `external_id` allows merge/upsert for OSM.
- `source` supports manual/user-suggested POIs.
- No raw OSM tags stored; only normalized fields.

---

## 3) OSM tag mapping (filter + normalize)

### Supported tags

- `amenity=cafe` -> `poi_type="cafe"`
- `amenity=restaurant` -> `poi_type="restaurant"`
- `leisure=park` -> `poi_type="park"`
- `shop=mall` -> `poi_type="mall"`

### Tag priority

- If multiple tags match, prefer `amenity` over `leisure`, `leisure` over `shop`.

---

## 4) Radius defaults by poi_type

- cafe: 40m (range 30-50)
- restaurant: 50m (range 40-70)
- park: 200m (range 100-300)
- mall: 120m (range 80-200)

Use fixed defaults for deterministic validation; optionally allow overrides for manual POIs.

---

## 5) Ingestion pipeline (simple and deterministic)

**Pipeline stages**

1. Fetch raw OSM data (Overpass or pre-exported extract).
2. Filter only supported tags.
3. Transform into internal POI model.
4. Upsert into `pois` by `(source, external_id)`.

**Do not** store raw OSM data in production tables.

---

## 6) Indexing for efficient lookup

- `pois(latitude, longitude)` composite index
- Optional PostGIS `GIST` index on `geography` point for fast radius queries

---

## 7) Example mapping function (OSM -> POI)

```py
OSM_TAG_MAP = {
    ("amenity", "cafe"): "cafe",
    ("amenity", "restaurant"): "restaurant",
    ("leisure", "park"): "park",
    ("shop", "mall"): "mall",
}

DEFAULT_RADIUS_M = {
    "cafe": 40.0,
    "restaurant": 50.0,
    "park": 200.0,
    "mall": 120.0,
}

TAG_PRIORITY = ["amenity", "leisure", "shop"]


def map_osm_to_poi(osm_item: dict) -> dict | None:
    tags = osm_item.get("tags", {})
    for key in TAG_PRIORITY:
        value = tags.get(key)
        if value is None:
            continue
        poi_type = OSM_TAG_MAP.get((key, value))
        if poi_type is None:
            continue
        name = tags.get("name") or f"{poi_type.title()}"
        return {
            "name": name,
            "poi_type": poi_type,
            "latitude": osm_item["lat"],
            "longitude": osm_item["lon"],
            "radius_m": DEFAULT_RADIUS_M[poi_type],
            "source": "osm",
            "external_id": str(osm_item.get("id")),
            "external_type": osm_item.get("type"),
        }
    return None
```

---

## 8) Example POI insert data

```sql
INSERT INTO pois (
  id, name, poi_type, latitude, longitude, radius_m,
  source, external_id, external_type, is_active, created_at, updated_at
) VALUES (
  gen_random_uuid(),
  'Highland Cafe',
  'cafe',
  10.7721,
  106.6980,
  40.0,
  'osm',
  '123456789',
  'node',
  true,
  now(),
  now()
);
```

---

## 9) Extensibility notes

- Manual POI: `source="manual"`, `external_id=NULL`.
- User suggested POI: `source="user"`, can be stored as inactive until approved.
- Merge strategy: when a manual POI is near an OSM POI, keep both or merge by admin rule (future feature).

---

## 10) Ingestion script

See [be/scripts/README_osm_ingest.md](be/scripts/README_osm_ingest.md) for a runnable CLI script.
