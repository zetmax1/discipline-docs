# Discipline Tracker — workspace

Public habit/discipline app in three separate git repos inside this folder:
- `discipline/` — web (React/TS, PWA). Owns `contracts/` (JSON Schema generated from zod).
  On GitHub this repo is called `discipline-front`; clone it into a folder named `discipline`,
  because the other repos' contract tests read `../discipline/contracts`.
- `discipline-back/` — API (Go/Gin), owns the DB, auth and migrations. From M4 also `cmd/worker`.
- `discipline-py/` — analytics (FastAPI), read-only DB access.
This folder itself only holds `docs/`, `.claude/` and this file (its own docs-only git repo). Ignore `_archive/`.

Product principles, glossary and time rules: `docs/product/VISION.md`. Current milestone: `docs/product/milestones/M{N}.md`. Release runbook: `docs/RELEASE.md`. Per-repo conventions load automatically from `.claude/rules/` when you touch that repo.

## Repos, setup & check commands
Each repo keeps its own `.env.example` (names only) and README.

**discipline/** (Node 22)
- Setup: `npm ci`. Env: `VITE_API_URL`, `VITE_TURNSTILE_SITE_KEY`, optional `VITE_SENTRY_*`.
- Run: `npm run dev` (http://localhost:8081). Test: `npm test`.
- Check: `npm run check` — tsc, eslint, vitest, build, `npm audit` against `audit-allowlist.json`, gitleaks.

**discipline-back/** (Go, toolchain pinned in `go.mod`; needs Postgres and Redis)
- Setup: `.env` from `.env.example`; locally also `APP_ENV=development`, `DB_SSLMODE=disable`.
- Migrate: `go run ./cmd/migrate up` (`status`, `down`). The server refuses to start on an old schema.
- Run: `go run ./cmd/server` (http://localhost:8080).
- Test: `make test` (starts `docker-compose.test.yml`: Postgres :55432, Redis :56379; `make test-down` stops it).
- Check: `make check` — go vet, staticcheck, `go test -race`, govulncheck, gosec (`.gosec-baseline.json`), gitleaks.

**discipline-py/** (Python 3.12)
- Setup: `python3.12 -m venv venv && venv/bin/pip install -r requirements-dev.txt`. Reads `../discipline-back/.env` if present.
- Run: `venv/bin/python main.py` (http://localhost:8082).
- Test: `make test` (starts `docker-compose.test.yml`: Postgres :55433). Needs `../discipline` checked out for the contract test.
- Check: `make check` — ruff, mypy, pytest, pip-audit, bandit (`.bandit-baseline.json`), gitleaks.

Each repo has one check command that runs lint, types, tests and vulnerability/secret scans: `make check` (discipline-back, discipline-py) / `npm run check` (discipline). Every check fails if any test was skipped. There is no CI yet; run the check command of every repo you touched before reporting. Never add to a baseline or allowlist without saying why in the commit.

## Workflow
- Work only on what the current task names. No drive-by refactors.
- Test first: a failing test that shows the behaviour, then the code, then green. Never weaken a check or delete a failing test to get green.
- **Base branch:** `main` in every repo. Branch from it, and rebase on it before asking for a merge.
- Branch `feat/M{N}` from the base branch in each repo you touch, same name everywhere. One commit per story or fix: `feat(M{N}): …` / `fix(M{N}): …`. Never push or merge without being told to.
- A contract change updates every affected repo in the same milestone; the design doc's rollout section gives the deploy order.
- Secrets: never hardcoded, printed or logged. Required secrets have no defaults; the app refuses to start without them. Keep each repo's `.env.example` current (names only).
- Never run anything against production or staging.
- If a decision isn't in the task or the design doc: stop and ask. Don't guess.

## Feature workflow
A feature prompt names an id (`F1`…`F14`) and spec items in `docs/product/milestones/`. Read only `VISION.md` and those items.
1. **Design** — write `docs/design/<id>.md`: stories with acceptance criteria; migrations (up + down); API + contract schemas; screens at 390 px and desktop with empty/loading/error/offline states; i18n keys; edge cases (timezone/DST, midnight, offline, several devices, new user); test plan; flag name; deploy order; open questions. Then **STOP** and wait for "go".
2. **Build** (after "go") — branch `feat/<id>` from the base branch in each touched repo.
   - Everything behind `FEATURE_<id>` (API env var → `GET /api/features`; the web hides disabled features).
   - Test first; one commit per story: `feat(<id>): …`.
   - Run each touched repo's check command.
   - Playwright screenshots at 390 / 1440 px into `docs/design/<id>-screens/`.
   - Report ≤ 25 lines, ending with owner steps: env vars, migrations, flags, deploy order.
3. **Deploy** — Railway deploys each repo on its own. Merge order: `discipline-back`, wait until
   its deploy is healthy, then `discipline-py`, then `discipline`. Every change must work with the
   previous schema and the previous version of the other services
   (expand → migrate → switch → contract).
4. Never push or merge.

## Product rules (from VISION.md)
- Every date/time is computed in the user's timezone; tests cover midnight and DST.
- Copy encourages, never shames. Rest is never shown as failure.
- No metric or claim without data behind it; never call rules "AI".
- Personal data: collect the minimum, never log it, include it in export and delete.

## Token discipline
- Don't read `docs/archive/` or `_archive/` unless asked.
- Read only the milestone and design files for the current task; use the Explore subagent for broad code searches.
- Run tests quietly; show only failures and the final counts.
- Reports: short, with file paths instead of pasted content. End with the owner's manual steps (env vars, migrations, Railway settings) as exact commands.
