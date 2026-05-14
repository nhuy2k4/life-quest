# AI Quest Schema Refinement (Production-Ready)

## 1. Final schema (clean, production-ready)

Below is a **clean** target schema designed for deterministic AI quests with GPS + POI + rule-based validation. Use this as Phase 2 target after safe migration.

### `quests`

```py
class Quest(Base, UUIDMixin, TimestampMixin):
   __tablename__ = "quests"

   template: Mapped[str] = mapped_column(String(255), nullable=False)
   labels: Mapped[list[str]] = mapped_column(JSON, nullable=False)  # multi-label target
   label_rules: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # {"coffee": 0.7, "cup": 0.5}
   min_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

   xp_reward: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
   is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

   # optional POI requirement
   poi_id: Mapped[uuid.UUID | None] = mapped_column(
      ForeignKey("pois.id", ondelete="SET NULL"),
      nullable=True,
   )
```

### `submissions`

```py
class Submission(Base, UUIDMixin):
   __tablename__ = "submissions"

   user_quest_id: Mapped[uuid.UUID] = mapped_column(
      ForeignKey("user_quests.id", ondelete="CASCADE"),
      nullable=False,
      unique=True,
   )

   image_url: Mapped[str] = mapped_column(String(500), nullable=False)
   cloudinary_public_id: Mapped[str] = mapped_column(String(255), nullable=False)
   file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

   vision_labels: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
   vision_raw: Mapped[dict | None] = mapped_column(JSON, nullable=True)

   lat: Mapped[float | None] = mapped_column(Float, nullable=True)
   lng: Mapped[float | None] = mapped_column(Float, nullable=True)
   location_accuracy_m: Mapped[float | None] = mapped_column(Float, nullable=True)
   location_captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

   poi_id: Mapped[uuid.UUID | None] = mapped_column(
      ForeignKey("pois.id", ondelete="SET NULL"),
      nullable=True,
   )
   poi_distance_m: Mapped[float | None] = mapped_column(Float, nullable=True)

   ai_score: Mapped[float | None] = mapped_column(Float, nullable=True)
   status: Mapped[SubmissionStatus] = mapped_column(
      sql_enum(SubmissionStatus, name="submission_status_enum"),
      nullable=False,
      default=SubmissionStatus.PENDING,
      index=True,
   )
   is_suspicious: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
   cheat_flags: Mapped[dict | None] = mapped_column(JSON, nullable=True)

   prev_distance_m: Mapped[float | None] = mapped_column(Float, nullable=True)
   time_delta_s: Mapped[float | None] = mapped_column(Float, nullable=True)
```

### `pois`

```py
class Poi(Base, UUIDMixin, TimestampMixin):
   __tablename__ = "pois"

   name: Mapped[str] = mapped_column(String(255), nullable=False)
   poi_type: Mapped[str] = mapped_column(String(50), nullable=False)  # cafe, park, mall
   latitude: Mapped[float] = mapped_column(Float, nullable=False)
   longitude: Mapped[float] = mapped_column(Float, nullable=False)
   radius_m: Mapped[float] = mapped_column(Float, nullable=False)
   is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
```

---

## 2. Diff from current schema (what changed + why)

1. **Quest label -> multi-label**

- Changed `quests.label` → `quests.labels` (JSON array).
- Why: reduce false negatives, allow semantic grouping and synonyms.

2. **Flexible confidence rules**

- Added `quests.label_rules` (JSON map) and optional `quests.min_confidence`.
- Why: allow per-label thresholds or global fallback without complex tables.

3. **POI metadata**

- Added `pois.poi_type`.
- Why: future filtering, analytics, and UI grouping (cafe/park/mall).

4. **Submission enriched**

- Added `vision_raw`, `poi_distance_m`, `lat/lng`, `location_accuracy_m`, `location_captured_at`.
- Why: debuggable, deterministic validation, GPS noise handling, and auditability.

5. **Anti-cheat improvements**

- `prev_distance_m`, `time_delta_s` to flag suspicious GPS movement.
- `file_hash` indexed (unique optional) for duplicate detection.

6. **Status system**

- Ensure enum includes: PENDING, PROCESSING, APPROVED, REJECTED, MANUAL_REVIEW.

---

## 3. Migration plan

### Phase 1 (safe, no breaking)

1. Add new columns:

- `quests.labels`, `quests.label_rules`, `quests.min_confidence`, `quests.template`
- `submissions.vision_labels`, `submissions.vision_raw`, `submissions.lat`, `submissions.lng`,
  `submissions.location_accuracy_m`, `submissions.location_captured_at`,
  `submissions.poi_id`, `submissions.poi_distance_m`, `submissions.prev_distance_m`, `submissions.time_delta_s`

2. Add table `pois` with `poi_type`.
3. Add indexes (see below).
4. Update pipeline/services to write new fields; stop using deprecated fields in code.

### Phase 2 (cleanup)

1. Drop deprecated fields:

- `quests.title`, `quests.description`, `quests.approval_rate`, `quests.difficulty`, `quests.location_required`

2. Migrate legacy quests → template + labels or archive.

---

## 4. Example data

### Example quests (multi-label)

```json
{
  "template": "Take a photo of a {label}",
  "labels": ["coffee", "cup", "drink"],
  "label_rules": {"coffee": 0.7, "cup": 0.5},
  "min_confidence": 0.6,
  "xp_reward": 50,
  "poi_id": null,
  "is_active": true
}

{
  "template": "Snap a {label} nearby",
  "labels": ["dog", "puppy", "pet"],
  "label_rules": {"dog": 0.65, "puppy": 0.6},
  "min_confidence": 0.6,
  "xp_reward": 70,
  "poi_id": "<uuid_of_park_poi>",
  "is_active": true
}
```

### Example submission

```json
{
  "user_quest_id": "<uuid>",
  "image_url": "https://.../img.jpg",
  "file_hash": "abc123...",
  "vision_labels": [
    { "label": "coffee", "score": 0.82 },
    { "label": "cup", "score": 0.64 }
  ],
  "vision_raw": { "labels": ["..."] },
  "lat": 10.7711,
  "lng": 106.6983,
  "location_accuracy_m": 18.2,
  "location_captured_at": "2026-05-06T10:11:22Z",
  "poi_id": "<uuid_of_cafe_poi>",
  "poi_distance_m": 42.5,
  "status": "approved"
}
```

---

## 5. Rule Engine compatibility

- **Multi-label matching**: `quests.labels` + `label_rules` allow relaxed matching while still deterministic. The engine passes if any label meets the rule threshold (or uses `min_confidence` fallback).
- **POI validation**: `submissions.poi_id` + `poi_distance_m` allow deterministic pass/fail with a radius check. This also supports "nearby" logic without external APIs.
- **Anti-cheat**: `prev_distance_m` + `time_delta_s` allow detection of unrealistic movement; `file_hash` supports duplicate detection.

---

## 6. Indexing

- `pois(latitude, longitude)` (or PostGIS `GIST` on geography point if enabled)
- `submissions(status)` (already indexed)
- `submissions(user_id, created_at)` (add)
- `submissions(file_hash)` (add; unique optional)
- `submissions(poi_id)` (add)
- `quests(labels)` (optional `GIN` JSON index if querying by label)

---

## 7. Backward compatibility

- Phase 1: keep legacy fields in DB but do not use in code/API.
- Phase 2: drop `quests.title`, `quests.description`, `quests.approval_rate`, `quests.difficulty`, `quests.location_required` once mobile/app is migrated.
