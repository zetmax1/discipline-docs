# F1 Review

## Summary
Review of feature F1 (the daily loop: block lifecycle, morning check-in, Today screen, focus sessions, block check-ins, evening shutdown) across discipline (web), discipline-back (API), and discipline-py (analytics).
Diffs were evaluated against base branch `feat/F12a` in all three repos.
Core daily loop flows, idempotent session replays, and offline sync mechanics are implemented cleanly. One High finding was identified regarding DST coverage (lack of autumn fall-back test and America/New_York zone testing), along with migration test fixture shape and owner items.

## Findings

### Incomplete DST test coverage: missing autumn fall-back and America/New_York tests
- **Severity:** High
- **Location:** `discipline-back/internal/handlers/daily_integration_test.go:104`, `discipline-py/tests/test_timezone_boundaries.py:1`
- **Description:** `daily_integration_test.go` verifies the spring-forward clock change (23:00 to 07:00 = 7 h in Europe/Berlin), but does not test the autumn fall-back clock change (e.g. 23:00 to 07:00 in America/New_York on 2026-11-01, where clocks jump back 02:00 -> 01:00 yielding 9 h = 540 minutes of elapsed sleep). In addition, daily handler tests for half-past midnight, skip defaults, and shutdowns rely exclusively on `Asia/Tashkent` (fixed UTC+5 without DST) and `UTC`. Similarly, `discipline-py/tests/test_timezone_boundaries.py` tests boundaries solely in `Asia/Tashkent` and `UTC` without a DST-observing zone.
- **Recommendation:** Add a test in `daily_integration_test.go` covering the autumn clock change with `America/New_York` asserting `sleepMinutes == 540`. Add `America/New_York` boundary tests in `discipline-py/tests/test_timezone_boundaries.py`.

### Migration 00008 test fixture does not cover all legacy schema shapes
- **Severity:** Medium
- **Location:** `discipline-back/internal/dbmigrate/dbmigrate_test.go:464`
- **Description:** `TestBlockLifecycleMigrationKeepsEveryBlock` seeds 4 rows covering 24:00 end, completed, skipped, and legacy end <= start. However, it does not include tasks with `source = 'plan'` and `plan_id` (added in migration 00006), 00:00 start times, or multi-user records to guarantee realistic production-shaped data integrity.
- **Recommendation:** Expand `TestBlockLifecycleMigrationKeepsEveryBlock` with plan-generated tasks, 00:00 midnight starts, and multi-user data.

### Offline sync creates exactly one session (verified)
- **Severity:** Low (Informational / Pass)
- **Location:** `discipline-back/internal/handlers/daily_integration_test.go:183`, `discipline/e2e/daily.spec.ts:11`
- **Description:** Verified that `TestFocusSession_OfflineReplayLeavesExactlyOneSessionWithTheRightData` replays the full client action queue twice for the same session UUID and validates that exactly one session row exists with correct final attributes. Playwright E2E offline test also passes cleanly.
- **Recommendation:** Keep current UUID primary key and repository upsert logic.

### Owner verification items
- **Severity:** Low
- **Location:** `docs/design/F1.md:113`
- **Description:** 
  1. Check-in actual times currently default to planned times rather than the span of linked focus sessions.
  2. Offline check-in made before midnight counts for the day it syncs if submitted across midnight.
  3. Top-3 and "later" actions in shutdown are deferred to F10.
- **Recommendation:** Owner to confirm these product decisions as noted in the status.

