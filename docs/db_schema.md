# Database Schema (ORM snapshot)

Source: SQLAlchemy models in `be/app/models/`. This document describes the current ORM structure (tables, key fields, and relationships).

## Core auth and users

### users

- Purpose: user accounts and profile data.
- Key fields: `id`, `username`, `email`, `password_hash`, `display_name`, `bio`, `avatar_url`, `provider`, `provider_id`, `role`, `is_verified`, `is_banned`, `onboarding_completed`, `level_id`, `xp`, `streak_days`, `trust_score`, `created_at`, `updated_at`.
- Relations: `level` (levels), `preference` (user_preferences), `refresh_tokens`, `posts`, `comments`, `likes`, `following`, `followers`, `notifications`, `badges`, `audit_logs`.

### levels

- Purpose: static leveling thresholds.
- Key fields: `id`, `name`, `required_xp`.
- Relations: `users`.

### refresh_tokens

- Purpose: refresh tokens (hashed) for sessions.
- Key fields: `id`, `user_id`, `token_hash`, `is_revoked`, `expires_at`, `created_at`.
- Relations: `user`.

### user_preferences

- Purpose: onboarding preferences and interest weights.
- Key fields: `id`, `user_id` (unique), `interests` (JSON list of category ids), `interest_weights` (JSON map), `activity_level`, `location_enabled`, `notification_enabled`.
- Relations: `user`.

## Quests and progress

### quests

- Purpose: quest definitions.
- Key fields: `id`, `title`, `description`, `template`, `vision_spec`, `labels`, `label_rules`, `min_confidence`, `xp_reward`, `difficulty`, `approval_rate`, `time_limit_hours`, `location_required`, `is_active`, `created_at`, `updated_at`.
- Relations: `categories` (M:N), `user_quests`.

### categories

- Purpose: quest categories.
- Key fields: `id`, `slug`, `name`, `icon`.
- Relations: `quests` (M:N).

### quest_categories

- Purpose: join table for quests <-> categories.
- Key fields: `quest_id`, `category_id` (composite PK).

### user_quests

- Purpose: per-user quest instance/status.
- Key fields: `id`, `user_id`, `quest_id`, `poi_id`, `status`, `started_at`, `expires_at`, `consolation_xp`.
- Constraints: unique per `(user_id, quest_id, poi_id)` with separate indexes for poi and non-poi.
- Relations: `user`, `quest`, `poi`, `submission`.

### quest_instances

- Purpose: mapping of user + quest + poi for location-bound quests.
- Key fields: `quest_id`, `user_id`, `poi_id` (composite PK), `created_at`.
- Relations: `quest`, `user`, `poi`.

## Submissions and social

### submissions

- Purpose: quest submissions (photo + metadata).
- Key fields: `id`, `user_quest_id` (unique), `image_url`, `cloudinary_public_id`, `file_hash`, `retry_count`, `exif_data`, `vision_labels`, `vision_raw`, `ai_metadata`, `lat`, `lng`, `location_accuracy_m`, `location_captured_at`, `poi_id`, `poi_distance_m`, `cheat_flags`, `ai_score`, `status`, `is_suspicious`, `rejection_reason`, `prev_distance_m`, `time_delta_s`, `created_at`.
- Relations: `user_quest`, `post`, `poi`, `ai_logs`.

### posts

- Purpose: social posts (often tied to submissions).
- Key fields: `id`, `submission_id` (unique), `quest_id`, `user_id`, `like_count`, `comment_count`, `image_url`, `caption`, `location_name`, `created_at`.
- Relations: `submission`, `quest`, `user`, `likes`, `comments`.

### follows

- Purpose: user follow graph.
- Key fields: `follower_id`, `following_id` (composite PK), `created_at`.
- Relations: `follower` (users), `following` (users).

### likes

- Purpose: post likes.
- Key fields: `user_id`, `post_id` (composite PK), `created_at`.
- Relations: `user`, `post`.

### comments

- Purpose: post comments with threading.
- Key fields: `id`, `post_id`, `user_id`, `parent_id`, `content`, `is_deleted`, `created_at`.
- Relations: `post`, `user`, `parent`, `replies`.

## Recommendation and analytics

### recommendation_logs

- Purpose: logging of recommendation events.
- Key fields: `id`, `user_id`, `quest_id`, `post_id`, `event`, `score`, `rank`, `request_id`, `algorithm_version`, `created_at`.
- Relations: `user`, `quest`, `post`.

### audit_logs

- Purpose: admin/user audit trail.
- Key fields: `id`, `actor_id`, `action`, `target_type`, `target_id`, `metadata`, `created_at`.
- Relations: `actor` (users).

### ai_detection_logs

- Purpose: AI detection trace per submission.
- Key fields: `id`, `submission_id`, `model_version`, `labels`, `ocr_text`, `confidence_stats`, `raw_response`, `created_at`.
- Relations: `submission`.

## Gamification

### xp_transactions

- Purpose: immutable XP ledger.
- Key fields: `id`, `user_id`, `submission_id`, `amount`, `source`, `created_at`.
- Relations: `user`, `submission`.

### badges

- Purpose: badge definitions.
- Key fields: `id`, `name`, `description`, `icon_url`, `rarity`, `category`, `criteria`, `is_hidden`, `is_active`, `sort_order`, `created_at`, `updated_at`.
- Relations: `user_badges`.

### user_badges

- Purpose: earned badges per user.
- Key fields: `id`, `user_id`, `badge_id`, `earned_at`.
- Relations: `user`, `badge`.

## Notifications and devices

### notifications

- Purpose: in-app notifications.
- Key fields: `id`, `user_id`, `type`, `data`, `is_read`, `created_at`.
- Relations: `user`.

### user_push_tokens

- Purpose: device push tokens.
- Key fields: `id`, `user_id`, `token` (unique), `provider`, `platform`, `is_active`, `created_at`, `last_seen_at`.

## POIs

### pois

- Purpose: points of interest.
- Key fields: `id`, `name`, `poi_type`, `latitude`, `longitude`, `radius_m`, `source`, `external_id`, `external_type`, `is_active`, `created_at`, `updated_at`.
- Constraints: unique (`source`, `external_id`).
- Relations: `submissions`.

## Notes

- The `experience.py` file is a placeholder and does not define tables yet.
- Enum fields are stored as strings via SQLAlchemy `Enum` (see `app/models/enums.py`).
