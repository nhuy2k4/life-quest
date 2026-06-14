# Recommendation V2 MVP Summary

## Goal

- Implement a rule-based recommendation system that is explainable, testable, and easy to debug.

## Completed

- Added `GET /recommendations/quests` to return sections, `request_id`, `score_breakdown`, and `reasons`.
- Added `POST /recommendations/log` and `POST /recommendations/events` for client-side interaction logging.
- Implemented candidate generation, rule scoring, cooldown, diversity reranking, and pagination in `app/services/recommendation/recommendation_service.py`.
- Ranking now derives directly from user preferences, posts, quest categories, user quest status, POI distance, freshness, and recommendation logs.
- Removed the old offline training path, model artifact flow, and ranker references.

## Main Files

- `app/models/recommendation.py`
- `app/schemas/recommendation.py`
- `app/services/recommendation/recommendation_service.py`
- `app/api/v1/recommendations.py`
- `tests/test_recommendation.py`

## Current Approach

Recommendation is rule-based only. It does not load a model, train offline artifacts, or use inference.
