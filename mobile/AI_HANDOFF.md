# AI Handoff - LifeQuest Mobile

Last updated: 2026-04-20

## 1) Project Goal

LifeQuest Mobile is an Expo Router + React Native app migrated from web flows, with route groups for auth/onboarding/main and reusable UI building blocks.

Primary target: continue shipping product flows (auth -> onboarding -> main feed -> quest/camera/post) while keeping architecture stable.

## 2) Current System Snapshot

### Runtime stack
- Expo 54 / React Native 0.81 / TypeScript
- File-based routing with Expo Router
- Root providers: AuthProvider -> UserProvider -> PostProvider

### Route architecture (current truth)
- Root stack in `app/_layout.tsx`
- Entry gate in `app/index.tsx`
- Route groups:
  - `app/(auth)`
  - `app/(onboarding)`
  - `app/(main)`
- Detail routes at root:
  - `app/post-detail.tsx`
  - `app/quest-detail.tsx`

### Route constants (single source)
- `constants/routes.ts` contains centralized route paths used by navigation calls.

### Shared state
- `contexts/AuthContext.tsx`: auth + onboarding completion flags
- `contexts/PostContext.tsx`: feed posts state
- `contexts/UserContext.tsx`: current user profile state

### Persistence
- `utils/storage.ts` wraps AsyncStorage with web/local fallback + memory fallback.
- Keys currently defined in `StorageKeys`:
  - `newPost`
  - `cameraMode`
  - `attachedQuest`
  - `suggestionFrom`

### UI system
- Product composites: `components/lifequest/*`
- UI primitives: `components/ui/*`
- Removed Expo starter UI/template dependencies from active flow.

## 3) What Was Done Already (Important History)

1. Replaced starter navigation approach with product route groups and root entry redirect.
2. Added and wired providers at root layout.
3. Implemented main product screens for auth, onboarding, feed, camera, quest-log, profile, notifications, settings, post/quest details.
4. Added shared components (BottomNav, PostCard, CommentSheet, ProfileHeader, etc.) and reusable primitives.
5. Added resilient storage service and integrated post/quest handoff behavior.
6. Removed template `(tabs)` and `modal` starter screens from runtime flow (folder `(tabs)` currently empty and can be deleted safely).
7. Standardized navigation by replacing hardcoded route strings with `constants/routes.ts`.
8. Latest validation status (at handoff time):
   - Diagnostics: no errors
   - Lint: pass (`LINT_EXIT:0`)

## 4) Known Gaps / Risks

1. `README.md` is still default Expo template and does not describe real app architecture.
2. `types/navigation.ts` duplicates route literals that now also exist in `constants/routes.ts` (risk of drift over time).
3. Need real runtime smoke test confirmation on device/simulator after route consolidation (auth -> onboarding -> main transitions, quest/camera/post loop).
4. Some screens still use mocked/static data; backend integration is not complete.

## 5) What AI Should Do Next (Priority Order)

### P0 - Stability checks
1. Run end-to-end smoke test for critical flows:
   - unauthenticated -> login
   - login -> onboarding intro/permission/username/interests
   - onboarding complete -> home
   - home -> quest-detail -> camera -> camera-result -> post -> home
   - home/post -> post-detail and quest-detail
2. Fix any route/runtime regressions found.

### P1 - Remove drift between route definitions
1. Align `types/navigation.ts` with `constants/routes.ts`.
2. Prefer deriving types from constants (or enforce one-direction mapping) so paths are not maintained in two places.

### P1 - Documentation correctness
1. Replace default `README.md` with project-specific setup and architecture notes.
2. Reference this file plus `convert-UI-skill.md` as onboarding docs for future contributors/AI sessions.

### P2 - Data/API migration
1. Replace mocked content in feed/quests/profile/notifications with API-backed data.
2. Keep screen-local UI state local; only lift shared state into contexts.
3. Keep persistence through `utils/storage.ts` only.

## 6) Working Rules for Future AI Edits

1. Preserve route-group architecture and provider chain unless explicitly changing app architecture.
2. Use `constants/routes.ts` for navigation targets; avoid inline path literals.
3. Do not reintroduce Expo starter screens/components into product flow.
4. For cross-screen handoff data, use `StorageKeys` and `utils/storage.ts`.
5. Prefer shared components in `components/ui` and `components/lifequest` before creating new duplicates.
6. After edits: run diagnostics + lint and report status.

## 7) Quick Start Prompt for New AI Conversation

Use this at the top of a new chat:

"Continue LifeQuest Mobile in this repo. Read `AI_HANDOFF.md`, `convert-UI-skill.md`, `app/_layout.tsx`, `app/index.tsx`, `constants/routes.ts` first. Keep current route-group architecture and provider chain. Use `constants/routes.ts` for all navigation changes. Validate with diagnostics and lint after edits."

## 8) Key Files to Read First (Minimum Set)

1. `AI_HANDOFF.md`
2. `convert-UI-skill.md`
3. `app/_layout.tsx`
4. `app/index.tsx`
5. `constants/routes.ts`
6. `contexts/AuthContext.tsx`
7. `contexts/PostContext.tsx`
8. `utils/storage.ts`
9. Target screen being edited + its route-group `_layout.tsx`
