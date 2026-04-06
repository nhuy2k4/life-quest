# LifeQuest Backend Project Rules

## 1. Architecture Rules

- **Layered Architecture:**
  - API layer: Handles only request/response
  - Service layer: Contains all business logic
  - Models: Database schema only (no business logic)
- **Never** put business logic in API routes or models
- **Always** put business logic in `services/`

## 2. Folder Structure Rules

- Follow strict structure:
  - `api/`: FastAPI routers (controllers)
  - `services/`: Business logic (by domain)
  - `models/`: SQLAlchemy models
  - `schemas/`: Pydantic schemas
  - `deps/`: Dependencies (auth, db)
  - `core/`: Config, security, database
  - `workers/`: Background tasks (Celery)
  - `services/ai/`: AI pipeline (vision, rules, scoring)
- Do **not** create new folders unless necessary

## 3. API Rules (FastAPI)

- Each API file:
  - Defines router only
  - Calls service functions
  - Handles request/response
- **Do not:**
  - Write DB queries in API
  - Write business logic in API
- **Example:**
  - Bad: Querying DB inside API
  - Good: Call service (e.g., `result = user_service.get_profile(user_id)`)

## 4. Service Layer Rules

- All business logic must be in `services/`
- Services can:
  - Access database
  - Call other services
  - Call AI module
- Services must be reusable and testable

## 5. Database Rules (SQLAlchemy)

- Models:
  - Only define schema
  - No logic
- Use:
  - UUID as primary keys
  - JSONB for flexible fields
  - Proper relationships
- **Never** write raw SQL unless necessary

## 6. AI Module Rules

- AI pipeline: image → vision → rules → scoring → result
- Structure:
  - `services/ai/`
  - `vision/`
  - `rules/`
  - `scoring/`
  - `pipeline/`
- Do **not** mix AI logic into other services

## 7. Async & Background Tasks

- Heavy tasks must use Celery:
  - AI processing
  - XP reward
  - Notifications
- API must **not** block waiting for AI

## 8. Naming Conventions

- `snake_case` for variables and functions
- `PascalCase` for classes
- Use clear, descriptive names
- Example: `get_user_profile` (good), `getData` (bad)

## 9. Error Handling

- Use centralized exceptions (`core/exceptions.py`)
- Do **not** raise raw exceptions in API

## 10. Security Rules

- Use JWT authentication
- Do **not** expose sensitive data
- Hash passwords (bcrypt)

## 11. Code Quality

- Keep functions small and focused
- Avoid duplicate logic
- Prefer readability over clever code

## 12. What NOT to do

- ❌ Do not mix layers
- ❌ Do not write huge files (>500 lines)
- ❌ Do not bypass service layer
- ❌ Do not hardcode config (use `.env`)

## 13. Goal

- Always generate code that is:
  - Scalable
  - Clean
  - Easy to maintain
  - Consistent with existing architecture
- If unsure, follow existing patterns in the project
