[CORE SKILLS]

- Converted web-style feature flows into React Native screens under app/(main), app/(auth), app/(onboarding) while preserving flow continuity (camera -> result -> post -> home, quest -> camera attach, auth -> onboarding).
- Replaced Expo template screen logic with product navigation redirection (app/(tabs)/index.tsx redirects to /(main)/home).
- Built reusable UI primitives and feature components used repeatedly across screens: Button/LQButton, Input/TextArea, Avatar, BottomSheetShell, BottomNav, PostCard, CommentSheet, ProfileHeader, LevelProgressBar.
- Standardized typed domain models in types/\* and consumed them across contexts/screens (Post, Quest, User).
- Implemented shared state with domain contexts (AuthContext, PostContext, UserContext) and mounted them at root provider chain in app/\_layout.tsx.
- Implemented resilient persistence service in utils/storage.ts with AsyncStorage + web localStorage + in-memory fallback, then integrated hydrate/persist flows in screens.
- Solved runtime rendering faults by normalizing primitive button children into Text inside components/ui/button.tsx.
- Solved camera API/runtime issues by moving to expo-camera CameraView + useCameraPermissions and safe-area overlay structure.

[ARCHITECTURE RULES]

- Data flow rule:
  - Screen-local transient UI state stays local (input values, toggles, modal open state).
  - Cross-screen mutable domain state goes to context (auth flags, post list).
  - Cross-session transfer/restore goes through utils/storage.ts with StorageKeys constants.
- Provider composition rule:
  - Root app wraps with AuthProvider -> UserProvider -> PostProvider in app/\_layout.tsx.
- Route-group rule:
  - app/(auth), app/(onboarding), app/(main) each has dedicated \_layout.tsx Stack with headerShown false.
- Module boundary rule:
  - app/\*: screen orchestration + navigation.
  - components/ui/\*: primitive reusable controls.
  - components/lifequest/\*: product-level composites.
  - contexts/\*: global state per domain.
  - utils/storage.ts + utils/validation.ts: shared services/validation.
  - types/\*: canonical interfaces exported via types/index.ts.
- Interaction rule:
  - Screens call contexts/services; components remain mostly presentation + local interaction.

[FILE ATTACHMENT RULES]

- Before implementing any screen task, required files must be provided/read in this order:
  1. Target screen file in app/\*.
  2. Related route layout file (\_layout.tsx in same group + root app/\_layout.tsx if navigation/provider impact exists).
  3. Related context file(s) in contexts/\* if state is shared.
  4. Related service file(s) in utils/\* (storage/validation/API adapter).
  5. Related shared component(s) in components/ui or components/lifequest used by the target screen.
- Required file types by task:
  - Navigation change: screen + group \_layout + root \_layout.
  - Shared state change: screen + context + types.
  - Persistence change: screen + utils/storage.ts + StorageKeys usage locations.
  - UI system change: target UI primitive + at least one consuming screen.
- Missing-file rule:
  - If any required file is missing, request the exact file path first.
  - Never assume hidden implementation details.

[WORKFLOW]

1. Audit current implementation in target flow (screen, context, service, navigation).
2. Preserve existing route and provider structure; avoid introducing new state layers unless required.
3. Convert UI into reusable pieces:
   - move repeated controls to components/ui,
   - move repeated product blocks to components/lifequest.
4. Add/align typed models in types/\* before wiring shared logic.
5. Implement screen logic with local state first, then lift to context only if cross-screen usage exists.
6. Add persistence only for data that must survive screen switch/restart (post handoff, quest attach metadata).
7. Integrate navigation transitions and params after state/persistence are stable.
8. Validate runtime issues (text rendering, camera permission path, storage null-module path).
9. Run lint/diagnostics and fix regressions in edited paths.
10. Keep placeholders only where product scope is intentionally pending; otherwise replace template content.

[PATTERNS]

- UI patterns:
  - Feed: FlatList + header + footer + fixed BottomNav + sheet overlays.
  - Card composition: PostCard/Quest cards use image block + action row + metadata + optional linked quest block.
  - Action controls: LQButton wraps Button variants; Input/TextArea handle label/error/helper consistently.
  - Bottom interactions: CommentSheet built on BottomSheetShell for reusable modal-sheet behavior.
- State patterns:
  - AuthContext stores isAuthenticated + onboardingCompleted.
  - PostContext stores posts + functional setPosts updates for prepend/de-dup hydration.
  - Screen state handles view toggles (showLocation, active tab, following flags, open sheets).
- Storage patterns:
  - Persist with setItem/saveItem using StorageKeys constants.
  - Hydrate in useEffect on destination screen (example: home hydrates StorageKeys.newPost).
  - Cleanup transfer keys after consumption (removeItem after hydrate/posting).
  - Fallback path always available (AsyncStorage failure -> web/local memory).

[DECISION RULES]

- Create custom hooks only when logic is reused across multiple screens/components and is not already solved by existing context/service.
- Use context when data is shared across screens in a route flow (auth status, post list); keep local state for screen-only UI concerns.
- Persist data when it must survive navigation boundary, app restart, or async handoff between flows (quest attach, newly created post handoff).
- Refactor into shared modules when:
  - UI fragment appears in >=2 screens,
  - same interaction model repeats,
  - or a bug fix must apply globally (example: button text wrapping fix at primitive level).

[ANTI-PATTERNS]

- Do not keep Expo starter/template screens as product screens once flow exists (explore/modal template content should not represent final product flow).
- Do not duplicate state copies across screen + context without a clear source of truth.
- Do not read/write AsyncStorage directly in many screens; route through utils/storage.ts.
- Do not leave primitive string children unwrapped in Pressable-based shared buttons.
- Do not place camera overlay content as children of camera preview when current SDK usage requires overlay outside preview component.
- Do not add persistence keys ad-hoc; register in StorageKeys.

[VALIDATION CHECKLIST]

- Screen uses existing route group and does not break current navigation paths.
- Required provider/context already mounted or intentionally added at root.
- Domain data shape matches types/\* interfaces.
- Shared UI uses existing primitives/composites before introducing new ones.
- Cross-screen data handoff uses StorageKeys + utils/storage.ts only.
- Hydration path includes de-duplication and cleanup removeItem when appropriate.
- Permission/error branches exist for camera/storage critical flows.
- No raw text rendering risk in shared button components.
- Lint and diagnostics pass after change.

[FINAL RULE SYSTEM]

- Rule 1: Start from existing flow files; never design from blank assumptions.
- Rule 2: Keep screen-local state local; promote only shared domain state to context.
- Rule 3: Persist only boundary-crossing data and always via utils/storage.ts + StorageKeys.
- Rule 4: Build UI in two layers: primitives (components/ui) then product composites (components/lifequest).
- Rule 5: Route and provider structure are stable contracts; modify only with explicit flow impact.
- Rule 6: Every reusable data contract must exist in types/\* before broad usage.
- Rule 7: Global bug fixes belong in shared primitives/services, not per-screen patches.
- Rule 8: Any task touching navigation/state/storage must include all required dependent files before edits.
- Rule 9: After implementation, enforce runtime branches (permission, fallback, cleanup) and run lint.
- Rule 10: Do not ship template placeholder screens as converted product screens.

[FINAL AGENT PROMPT]
You are migrating and extending a multi-screen React Native Expo app with existing route groups, shared contexts, and storage handoff.
Use current project files as source of truth; do not assume hidden architecture.
Read target screen + related layout + context + service + shared component files before editing.
Keep local UI state in screen, shared domain state in context, boundary data in utils/storage.ts with StorageKeys.
Prefer existing components in components/ui and components/lifequest; refactor duplicates into shared modules.
Maintain types in types/\* and update interfaces before wiring cross-screen logic.
Preserve provider chain in app/\_layout.tsx and route-group layout contracts.
For camera/storage flows, keep permission/error/fallback branches explicit.
Apply global fixes at primitive/service level, not repeated screen patches.
Clean up one-time storage keys after hydration.
Run lint/diagnostics after edits and fix introduced issues.
Avoid Expo template placeholders for product routes.
If any required file is missing, request exact path and stop assumptions.
Return concise change summary with impacted files and verification status.
