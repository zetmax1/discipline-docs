# F12a Review

## Summary
Review of feature F12a (Uzbek/Russian/English i18n, dark mode, and mobile app shell) across discipline (web), discipline-back (API), and discipline-py (analytics).
Diffs were evaluated against base branch `feat/F0` (web, API) and `fix/phase-5` (analytics).
All acceptance criteria S1–S6 are implemented; error codes are stable and verified against JSON Schema contracts; locale and theme switching function cleanly. One High finding in web audit checks and two Medium findings were identified.

## Findings

### Web audit allowlist missing recently published glob and minimatch advisories
- **Severity:** High
- **Location:** `discipline/audit-allowlist.json:1`
- **Description:** `npm run check` fails at `audit:check` because `npm audit --omit=dev` reports two new moderate advisories in `sucrase` (transitive dependency of `tailwindcss`): `GHSA-3g3m-2fjr-6pw4` (glob) and `GHSA-g3hv-75wg-m249` (minimatch). These are build-time only dependencies for Tailwind CSS compilation.
- **Recommendation:** Add reviewed entries for `GHSA-3g3m-2fjr-6pw4` and `GHSA-g3hv-75wg-m249` to `audit-allowlist.json` documenting that sucrase is executed solely during Vite/Tailwind build with local configuration files.

### Analytics test isolation dependent on external DB_SSLMODE environment
- **Severity:** Medium
- **Location:** `discipline-py/tests/conftest.py:8`
- **Description:** `test_engine_uses_sslmode` in `tests/test_db_sslmode.py` fails when `discipline-back/.env` is present with `DB_SSLMODE=disable` (the standard local dev setting from CLAUDE.md), because `app.config` imports the parent `.env` before test overrides apply.
- **Recommendation:** Add `"DB_SSLMODE": "require"` to `TEST_ENV` in `tests/conftest.py` so unit tests execute in a hermetic environment independent of local development `.env` configurations.

### Uzbek and Russian translations require native speaker verification
- **Severity:** Low
- **Location:** `discipline/src/i18n/uz.ts:1`, `discipline/src/i18n/ru.ts:1`
- **Description:** Dictionaries provide complete key parity and parameterization, but copy was author-drafted and pending owner / native speaker review as noted in design doc owner items.
- **Recommendation:** Keep on owner backlog for native speaker review prior to production rollout.

### Five colour tokens adjusted for WCAG AA contrast pending owner approval
- **Severity:** Low
- **Location:** `discipline/src/index.css:12`
- **Description:** Five token values were adjusted to satisfy WCAG AA 4.5:1 contrast requirements (tested in `src/theme/contrast.test.ts`).
- **Recommendation:** Confirm token aesthetics with the product owner before removing the `FEATURE_F12A` flag.

