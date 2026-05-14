# OSM POI Ingestion Script

This script ingests OSM POIs (cafe, restaurant, park, mall) into the `pois` table.

## Usage

```bash
# from d:\DATN\be
python scripts/osm_ingest.py --south 10.75 --west 106.65 --north 10.80 --east 106.72
```

### Optional flags

- `--overpass-url` Override Overpass API endpoint.
- `--dump-json` Print a sample of mapped POIs as JSON.
- `--dump-limit` Limit JSON preview (default 10).

## Notes

- The script uses a deterministic radius by `poi_type`.
- Upsert is based on `(source, external_id)`.
- Raw OSM payload is not stored.
