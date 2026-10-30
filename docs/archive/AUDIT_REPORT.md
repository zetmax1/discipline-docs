Commit IDs refer to the archived monorepo.

# Discipline Tracker — Security & Correctness Audit

- **Date:** 2026-10-29
- **Scope:** `discipline/` (React + TypeScript frontend), `discipline-back/` (Go/Gin API), `discipline-py/` (Python/FastAPI analytics), plus each project's git history.
- **Mode:** Read-only at audit time (§1–§8 are the original findings). §0 records the remediation status after fix phases 1–5.
- **Original audit mode:** No project code was changed. Tools ran from a separate scratch directory. **No requests were sent to the production deployment.** The only outbound calls were package-registry and vulnerability-database lookups, plus one request to the public dictionary API (`api.dictionaryapi.dev`) to check suspicion #6.

> **Where the code differs from the brief:** The frontend is **TypeScript**, not JS. The Go backend has **no commitments, goals, or schedules tables or routes**. Commitments and goals exist only in React state on the Smart Schedule page and are sent to Python for each generation. The database has 3 tables (users, tasks, vocabulary_words). **There is no 12-hour vocabulary job.** Words are created when a request needs them (see F-14).

---

## 0. Remediation status (updated 2026-10-30, after fix phases 1–5)

**Nothing is deployed yet.** Phases 1–5 are on `fix/phase-5` in the monorepo (`apps/api`, `apps/analytics`, `apps/web`); production still runs the pre-phase-1 code from the three old repositories. No finding is therefore labelled plain "Fixed".

Labels:
- **Fixed in code — pending deploy:** the fix is complete and tested; it takes effect when released (`docs/RELEASE.md`).
- **Fixed in code — pending deploy + manual step:** as above, plus a step only you can do (named in the last column).
- **Partial:** part of the finding remains open; the last column says what is missing.

Counts: 21 pending deploy, 3 pending deploy + manual step, 5 partial.

Commit IDs are monorepo commits. The histories were rewritten into `apps/` when the repositories were combined, so the IDs differ from the ones in the old repositories. Contract changes are listed in `API_CHANGES.md`.

| ID | Status | Commits | Notes / what is missing / manual step |
|---|---|---|---|
| F-01 | Fixed in code — pending deploy | 3cd22f4 | — |
| F-02 | Fixed in code — pending deploy + manual step | c100607, bd9534b | Rotate `JWT_SECRET` and `INTERNAL_JWT_SECRET` on deploy; any secret that may have run on a default is compromised (RELEASE §4 step 2). |
| F-03 | Fixed in code — pending deploy + manual step | b1d08a9, 21f648d | Remove the analytics service's public domain on Railway (RELEASE §4 step 5). |
| F-04 | Fixed in code — pending deploy + manual step (blocks public launch) | 55e2f18, 279015d, 08d058d, ad8f74b, f6aa7a8 | Spoofed `X-Forwarded-For` no longer works, limits live in Redis, authenticated requests count per user and the per-email lockout is gone. **Until the client-IP header is confirmed with `/debug/ip` on staging and `TRUSTED_PROXIES`/`TRUSTED_IP_HEADER` are set, every anonymous client on Railway looks like the proxy's address: the per-IP limits (5/min on `/api/auth/*`, 30 login failures per 15 min) then apply to all users together** (RELEASE §1.1). |
| F-05 | Fixed in code — pending deploy | 70bb630, dd01dd1, c5253bf | — |
| F-06 | Fixed in code — pending deploy | 2e70507, f64e9ed, eaf4574, 80211fd | The schema now lives in `packages/contracts/`. |
| F-07 | Fixed in code — pending deploy | 052a99a, ec43aea, 3cd2781 | — |
| F-08 | Partial | 5f5c5f3, a63a553, b57be8e, 39bb652 | Missing: the scheduling algorithm redesign (deferred to the next stage); an overnight commitment still blocks the same day's morning. |
| F-09 | Fixed in code — pending deploy | c11c856 | — |
| F-10 | Fixed in code — pending deploy | 932423d, 32f1b5f, 81a67ee | Existing invalid/overlapping rows are kept and stay editable (checks apply to writes). Skipped blocks no longer count as overlapping. |
| F-11 | Fixed in code — pending deploy | c558c2e | — |
| F-12 | Fixed in code — pending deploy | ab2fa69 | — |
| F-13 | Fixed in code — pending deploy | 9f31109 | Charts stay server-side (moving rendering to the client was deferred by instruction). |
| F-14 | Fixed in code — pending deploy | 4e1e894, 82052d3 | — |
| F-15 | Fixed in code — pending deploy | b0fe708, d31cc1a | The hardcoded CEFR badge is removed; there is no CEFR data. The vocabulary source redesign is a separate next-stage item. |
| F-16 | Fixed in code — pending deploy | 12affb7 | — |
| F-17 | Fixed in code — pending deploy | 3e9bc8b, cdec50b | A body over 1 MB without `Content-Length` is still rejected, with 400 from the JSON binder instead of 413. |
| F-18 | Partial | 7e308f7, 7623cc3 | Done: 24h tokens, revocation on logout and password change. Missing: the token still lives in `localStorage` and there is no Content-Security-Policy (no XSS sink was found). |
| F-19 | Partial | 3d1334e | Done: the file is removed from the tree. Missing: the 50 credentials are still in git history (by instruction, not rewritten). The monorepo imported that history (`069f550`), so they go wherever it is pushed. Rotate or delete the 50 accounts **before** pushing, and keep the repository private. |
| F-20 | Fixed in code — pending deploy | 35b5f99, e6def33 | — |
| F-21 | Fixed in code — pending deploy | 0fcb9fc, 44423e5 | — |
| F-22 | Fixed in code — pending deploy | e2017d2, c8dc19a, 49ed46d | Swagger `docs/` regenerated; a test fails when it drifts from the router. |
| F-23 | Fixed in code — pending deploy | e75648e, 0f2001e | — |
| F-24 | Fixed in code — pending deploy | 6598437, edd1a8b | — |
| F-25 | Fixed in code — pending deploy | 8da1ff3 | — |
| F-26 | Partial | 73eda6e, 57f6e5e, 45dab80, 11699fe, c920af0 | Missing: react-router 6 → 7 and zod 3 → 4 (three npm advisories, reviewed as not reachable, listed in `apps/web/audit-allowlist.json`; CI fails on anything else); x/crypto GO-2026-5932 has no fix (not called). |
| F-27 | Fixed in code — pending deploy | 3a9e14b, f853bbc, 4222fed | — |
| F-28 | Fixed in code — pending deploy | a40fc32, 614aeca, 3cfb0e4 | `vocabulary_words.date` is now DATE too (migration 00007). |
| F-29 | Partial | 67957df, d5ba902, 924b397 | Done: saving a week is idempotent and a clash shows the server's 409 message. Missing: commitments and goals are still kept only in the browser (`localStorage`); server-side persistence is deferred to the redesign. |

### Re-audit (same tools as §6, run on `fix/phase-5`; every one of them now runs in CI)

| Tool | Before (§6) | After phase 4 | After phase 5 |
|---|---|---|---|
| `go vet` / `staticcheck` | 0 / 0 | 0 / 0 | 0 / 0 (staticcheck v0.8.2) |
| `gosec` | 4 × G404 (false positives) | same | not re-run in phase 5 |
| `govulncheck` | 17 called | 0 called | **0 called** (v1.9.0); x/crypto GO-2026-5932 has no fix and is not called |
| `go test -race` | no tests | 200 tests | **250 test cases (176 top-level), 13 packages, 0 skipped**, with Postgres and Redis |
| `ruff` | 92 | 53 (style) | **0** (ruff 0.17.1 pinned, config in `pyproject.toml`) |
| `mypy` | 17 | 28 | **0** (mypy 2.4.0 pinned) |
| `bandit` | 1 (B104) | 3 false positives | not re-run in phase 5 |
| `pip-audit` | 28 entries | 0 | **0** |
| `pytest` | 2 tests | 244 | **255, 0 skipped** (incl. real Postgres and the contract test) |
| `npm audit --omit=dev` | — (full: 32) | 13 | **3**, all reviewed and allowlisted (react-router ×2, zod); CI fails on any other |
| `eslint` | 15 errors, 8 warnings | 6 errors, 7 warnings | **0 errors**, 7 warnings (react-refresh hints) |
| `tsc` / build / vitest | clean / OK / 1 test | clean / OK / 67 | clean / OK / **81 tests** |
| `gitleaks` | could not run | 7 hits (test dummies) | **0** with `.gitleaks.toml` (default rules; four exact dummy values allowed) |

### Still open (outside the 29 findings or explicitly deferred)
- **Client-IP header on Railway** (F-04): must be confirmed on staging before a public launch.
- **Smart schedule algorithm and vocabulary source:** redesign planned for the next stage.
- **Dependency majors:** react-router 7 and zod 4 (clear the allowlisted advisories).
- **Token storage:** `localStorage` without a CSP (F-18).
- **Credentials in git history** (F-19): rotation pending; history not rewritten.

---

## 1. Executive summary

**Overall risk: HIGH.** One confirmed critical flaw lets any registered user read any other user's analytics. Several hardcoded fallback secrets would allow full account takeover if a production environment variable is missing. Everything else is mostly correctness and reliability problems that make the analytics numbers and "AI" text misleading.

**Top 5 issues**
1. **F-01 (Critical, Confirmed):** Query-parameter injection in the Gin→FastAPI proxy. A request to `GET /api/analytics/focus-patterns?days=30%26user_id%3D<victim>` returns the victim's focus analytics. Reproduced end to end against the real Go and FastAPI parsing code.
2. **F-02 (High, Confirmed in code / prod needs confirmation):** Hardcoded fallback `JWT_SECRET`, `ADMIN_PASSWORD=admin123`, and analytics API keys are committed to source. If `JWT_SECRET` is unset in production, anyone with the source can forge a token for any user.
3. **F-04 (High, Likely):** `gin.Default()` trusts every proxy, so `c.ClientIP()` returns an attacker-chosen `X-Forwarded-For` value. That bypasses all per-IP rate limits, including login brute-force protection.
4. **F-03 (High, Likely):** The FastAPI service sits on a public Railway domain, takes `user_id` straight from the query string, and is protected only by one static shared key. A leaked key exposes every user's data.
5. **F-05 (High, Confirmed):** "Today" is computed in UTC on both client and server. A UTC+5 user who adds blocks between 00:00 and 04:59 local time has them stored under yesterday's date. A weekly plan saved in that window is written one day early.

Also notable: the Analytics page's "AI detected patterns" card and trend badge can never show data because of contract mismatches (F-06). The same "Focus Score" label is computed with three different formulas (F-07). The schedule generator ignores goals below 5 hours and says it "learned your preferences" even with no history (F-08).

---

## 2. System map

### 2.1 Services and entrypoints

| Service | Path | Entrypoint / start | Deploy hints |
|---|---|---|---|
| Frontend (React 18 + Vite + TS, react-query) | `discipline/` | `npm start` → `serve dist -s -l tcp://0.0.0.0:$PORT` (`package.json:9`) | Static SPA. API base from `VITE_API_URL` (`src/lib/api.ts:2`) |
| Main API (Go 1.25, Gin 1.11, GORM, Postgres) | `discipline-back/` | `cmd/server/main.go` → `config.Load` → `ConnectDB` (AutoMigrate) → `SeedAdmin` → `gin.Default()` → `r.Run(":"+PORT)` | Multi-stage `Dockerfile` (`golang:alpine` → `alpine:latest`, runs as root) |
| Analytics (FastAPI 0.115, SQLAlchemy, pandas, matplotlib/seaborn) | `discipline-py/` | `Procfile`: `uvicorn main:app --host 0.0.0.0 --port $PORT` (single worker) | Railway/Nixpacks |

### 2.2 HTTP routes

**Gin (`internal/routes/routes.go`)**. Global middleware runs in this order: security headers → global rate limit (100/min/IP) → CORS.

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/swagger/*any` | No | Swagger UI is public |
| GET | `/ping` | No | Health check |
| POST | `/api/auth/register`, `/api/auth/login` | No | Auth rate limit of 5/min/IP |
| GET, PUT | `/api/me` | JWT | Profile read/update |
| POST | `/api/tasks`, `/api/tasks/bulk` | JWT | Bulk insert has no size cap |
| GET | `/api/tasks?date=` | JWT | Defaults to the server's UTC date |
| PUT, DELETE | `/api/tasks/:id` | JWT | Filtered by `user_id` ✔ |
| GET | `/api/dashboard/stats?date=` | JWT | **Not used by the frontend** |
| GET | `/api/analytics?range=week\|month` | JWT | Proxies to Py `/analytics/weekly\|monthly`; analytics rate limit 10/min/IP |
| GET | `/api/analytics/focus-patterns?days=` | JWT | Proxies to Py. **Vulnerable (F-01)** |
| POST | `/api/analytics/smart-schedule` | JWT | Raw request body streamed to Py |
| GET | `/api/quote` | JWT | Calls zenquotes.io; cached for 2–3 hours |
| GET | `/api/vocabulary/today?date=`, `/api/vocabulary?lang=&page=&pageSize=` | JWT | Lazy word creation (F-14) |
| PUT | `/api/vocabulary/:id/learned`, `/:id/saved` | JWT | Filtered by `user_id` ✔ |
| POST | `/api/admin/register` | JWT + role=admin | Creates admin accounts |

**FastAPI (`main.py`, `app/api/analytics_api.py`, `app/smart_schedule/router.py`)**

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/`, `/health` | No | |
| GET | `/docs`, `/redoc`, `/openapi.json` | No | FastAPI defaults; not disabled |
| GET | `/analytics/weekly`, `/analytics/monthly` | `X-API-Key` | `user_id` comes from the query string |
| GET | `/analytics/productivity-trend` | `X-API-Key` | **Gin does not proxy it.** It is the only endpoint that returns `insights` (see F-06) |
| GET | `/analytics/focus-patterns` | `X-API-Key` | `user_id`, `days` (7–365) |
| POST | `/analytics/smart-schedule` | `X-API-Key` | `user_id` from the query string; commitments and goals in the body |

### 2.3 How Gin and FastAPI communicate

- **HTTP plus a shared database.** Gin calls Python over HTTP (`PYTHON_SERVICE_URL`, default `https://discipline-py.up.railway.app`, `routes.go:79`). It sends the user's ID from the JWT as `?user_id=<id>` and a static `X-API-Key` header.
- Python then **reads the `tasks` table directly** from the same Postgres database (`app/database.py`). It uses the same DB credentials, so it has write privileges even though it only reads.
- FastAPI identifies the user **only by the `user_id` query parameter**. It does no verification beyond the shared key.

### 2.4 Database (GORM `AutoMigrate` only; no versioned migrations)

| Table | Columns | Indexes / constraints | Written by | Read by |
|---|---|---|---|---|
| `users` | id, name, email, password (bcrypt, cost 10), role, created_at, updated_at | unique(email) | Go | Go |
| `tasks` | id, user_id, name, category, start_time *(varchar "HH:MM")*, end_time *(varchar)*, status, distractions, energy, date *(varchar "YYYY-MM-DD")*, timestamps | index(user_id), index(date). No composite index, no FK | Go | Go, Python |
| `vocabulary_words` | id, user_id, word, language, definition, example, synonym, part_of_speech, date *(varchar)*, learned, saved, timestamps | index(user_id), index(date). **No unique key** | Go | Go |

Python declares ORM mirrors for `tasks` and `users` (`app/models/task.py`, `app/models/schedule.py`). They match the Go columns, and the `User` mirror is unused.

### 2.5 Background and scheduled work

- **No cron jobs, tickers, or scheduler exist in any service.** I grepped for ticker, cron, `AfterFunc`, `BackgroundTasks`, `lifespan`, and `setInterval`.
- In-process state that is lost on restart and **separate per instance**:
  - Per-IP rate-limiter maps, plus one cleanup goroutine per limiter (`rate_limiter.go:25`).
  - The quote cache (`quote_handler.go`).
- Vocabulary is created inside `GET /api/vocabulary/today` (F-14). The client re-queries at most every 12 hours (`use-vocabulary.ts:33`, `staleTime`), which is probably where the "12 hours" belief comes from.
- With 2+ instances, rate limits multiply by the instance count and the vocabulary inserts can race (F-14).

### 2.6 Configuration and external APIs

| Var | Service | Fallback when unset |
|---|---|---|
| `DB_HOST`/`DB_PORT`/`DB_USER`/`DB_NAME` | Go, Py | localhost/5432/postgres/discipline |
| `DB_PASSWORD` | Go, Py | Go: `postgres`. **Py: `zetmax111`**, which matches the developer's local DB password |
| `JWT_SECRET` | Go | **Hardcoded 70-char string** (`config.go:43`) |
| `JWT_EXPIRY_HOURS` | Go | 72 |
| `ALLOWED_ORIGINS` | Go | localhost and Railway URLs (unused; see F-21) |
| `ANALYTICS_API_KEY` | Go, Py | Go: `development_internal_analytics_key`. Py: a different hardcoded string |
| `ADMIN_EMAIL`/`ADMIN_PASSWORD`/`ADMIN_NAME` | Go | `admin@discipline.app` / **`admin123`** / Admin |
| `PYTHON_SERVICE_URL` | Go | `https://discipline-py.up.railway.app` |
| `PORT` | Go, Py, FE | 8080 / 8082 |
| `ANALYTICS_PORT`, `ANALYTICS_HOST`, `HOST` | Py | 8082 / 0.0.0.0 |
| `VITE_API_URL` | FE (build time) | `http://localhost:8080/api` |
| `GIN_MODE` | Go (implicit) | Not set in code, so Gin runs in debug mode |

Python also loads `../discipline-back/.env` (`app/config.py:10`).

**External calls:**
- `api.dictionaryapi.dev` (Go, 5s timeout)
- `zenquotes.io` (Go, 5s timeout)
- Gin→Python HTTP (**no timeout**; F-17)

---

## 3. Findings table

| ID | Severity | Category | Location | Title | Status |
|---|---|---|---|---|---|
| F-01 | **Critical** | Security | `discipline-back/internal/handlers/analytics_handler.go:98-103` | Query-param injection in the analytics proxy exposes other users' data | Fixed in code (pending deploy) |
| F-02 | High | Security | `discipline-back/config/config.go:43,47`, `config/seed.go:24`, `discipline-py/app/config.py:25,46` | Hardcoded fallback secrets (JWT, admin password, API keys, DB password) | Fixed in code (pending deploy + manual) |
| F-03 | High | Security | `discipline-py/app/api/analytics_api.py:27-29,45`, `routes.go:79` | Public analytics service trusts `user_id` and relies on one static key | Fixed in code (pending deploy + manual) |
| F-04 | High | Security | `discipline-back/cmd/server/main.go:58`, `middleware/rate_limiter.go:39` | Rate limits bypassable via a spoofed `X-Forwarded-For` | Fixed in code (pending deploy + manual) |
| F-05 | High | Bug | `discipline/src/hooks/use-tasks.ts:19`, `pages/Planner.tsx:37`, `pages/SmartSchedule.tsx:79`, `task_handler.go:174` | UTC "today" stores blocks and saved plans under the wrong date for UTC+5 users | Fixed in code (pending deploy) |
| F-06 | Medium | Bug | `discipline/src/pages/Analytics.tsx:98,156` | "AI detected patterns" and the trend badge can never show data (contract mismatch) | Fixed in code (pending deploy) |
| F-07 | Medium | Bug | `Dashboard.tsx:38`, `task_service.go:143-144`, `metrics_service.py:128-130` | "Focus Score" has three different formulas | Fixed in code (pending deploy) |
| F-08 | Medium | Bug | `discipline-py/app/smart_schedule/generator.py:53-76` | Schedule generator ignores goals, ignores minutes, crashes on bad input, and claims to learn without data | Partial |
| F-09 | Medium | Bug | `discipline/src/pages/SmartSchedule.tsx:28,36,107` | User-added commitments always apply to Monday only | Fixed in code (pending deploy) |
| F-10 | Medium | Bug | `task_handler.go:30-44`, `task_service.go:87-96` | No server-side validation of task times, dates, overlaps, or update fields | Fixed in code (pending deploy) |
| F-11 | Medium | Reliability | `discipline-py/app/visualization/charts.py:173` | Any completed zero-duration task makes the Analytics page return 500 | Fixed in code (pending deploy) |
| F-12 | Medium | Bug | `focus_heatmap.py:44-56`, `focus_service.py:84-87` | Heatmap color scale and hour bucketing are wrong | Fixed in code (pending deploy) |
| F-13 | Medium | Reliability/Perf | `analytics_api.py:44,172`, `visualization/*.py` | pyplot used from a threadpool; unbounded CPU-heavy rendering | Fixed in code (pending deploy) |
| F-14 | Medium | Reliability | `vocab_service.go:34-72`, `models/vocabulary.go` | No vocabulary job: gaps, duplicates, permanent fallback text, unvalidated date | Fixed in code (pending deploy) |
| F-15 | Medium | Bug | `vocab_service.go:248-257`, `Vocabulary.tsx:64` | Wrong dictionary sense and part of speech; CEFR labels are hardcoded | Fixed in code (pending deploy) |
| F-16 | Medium | Bug | `weekly_analysis.py:45-50`, `productivity_service.py:57-58` | Future-dated tasks deflate weekly completion and zero the streak | Fixed in code (pending deploy) |
| F-17 | Medium | Reliability | `analytics_handler.go:65,112,159,167`; `task_handler.go:50`; `task_service.go:46-54` | No timeouts or body limits; unbounded, non-transactional bulk insert | Fixed in code (pending deploy) |
| F-18 | Low | Security | `discipline/src/lib/api.ts:7,143`; `auth_service.go:148-157` | 72h JWT in localStorage with no revocation on logout or password change | Partial |
| F-19 | Medium | Security | `discipline-back/fake_users_credentials.csv` (tracked) | 50 plaintext credentials committed to git | Partial |
| F-20 | Medium | Security | `discipline-back/config/database.go:16` | Postgres connection forces `sslmode=disable` | Fixed in code (pending deploy) |
| F-21 | Low | Security | `cors_middleware.go:25-27`; `discipline-py/main.py:23-29`, `config.py:42` | CORS reflects every Origin; Python uses `*` with credentials | Fixed in code (pending deploy) |
| F-22 | Low | Security | `routes.go:38`, `main.go:58`, `discipline-py/main.py:15` | Public Swagger and `/docs`; Gin debug mode by default | Fixed in code (pending deploy) |
| F-23 | Low | Security | `auth_service.go:51-53,84-87`; `auth_handler.go:28` | User enumeration on register; weak password rules | Fixed in code (pending deploy) |
| F-24 | Low | Security | `auth_handler.go:200-205`; `auth_service.go:118-124` | Email change needs no password and no format validation | Fixed in code (pending deploy) |
| F-25 | Low | Security | `discipline-back/Dockerfile:1,16,25` | Unpinned base images; container runs as root | Fixed in code (pending deploy) |
| F-26 | Low | Security | `go.mod`, `requirements.txt`, `package.json` | Dependency CVEs (none confirmed reachable in a harmful way) | Partial |
| F-27 | Low | Bug | `Planner.tsx:190-194`, `Login.tsx:36`, `Analytics.tsx:20-22`, `api.ts:68-74` | Frontend: lost distraction updates, stale error, demo-mode redirect loop | Fixed in code (pending deploy) |
| F-28 | Low | Quality | `models/task.go`, `task_repository.go:61-65`, `database.go`, `app/database.py:13` | String-typed times and dates, missing composite index and FK, masked DB errors, pool defaults | Fixed in code (pending deploy) |
| F-29 | Low | Bug | `SmartSchedule.tsx:53-91` | Commitments and goals not persisted; "Save Weekly Plan" is not idempotent | Partial |

---

## 4. Finding details

### F-01 — Query-parameter injection in the analytics proxy exposes other users' data
- **Severity:** Critical · **Confidence:** Confirmed (reproduced locally against the real Go and FastAPI parsing)
- **Location:** `discipline-back/internal/handlers/analytics_handler.go:98-103`, `discipline-py/app/api/analytics_api.py:172-175`
- **Evidence:**
  ```go
  days := c.Query("days")            // URL-decoded, attacker-controlled
  ...
  endpoint := fmt.Sprintf("%s/analytics/focus-patterns?user_id=%d&days=%s", h.pythonServiceURL, userID, days)
  ```
- **What's wrong:** Go decodes `days`, then pastes it unescaped into the upstream query string. If `days` is `30%26user_id%3D2`, Go decodes it to `30&user_id=2`, so the outbound query becomes `user_id=1&days=30&user_id=2`. FastAPI (Starlette) uses the **last** value for a scalar query parameter.
- **Reproduction (local, in the scratch directory):**
  - Go: `outbound RawQuery: user_id=1&days=30&user_id=2`
  - FastAPI 0.115 TestClient on the same query: `{'user_id': 2, 'days': 30}`
- **Impact:** Any registered user (registration is open) can read any other user's focus data. That includes the deep-work heatmap by weekday and hour, peak hours, per-weekday focus and completion averages, the daily distraction series (which reveals the dates the person was active), and deep-work distribution. User IDs are sequential, so every user can be enumerated.
- **How to reproduce:**
  1. Run the stack locally and register two users, A and B. Give B some completed deep-work tasks.
  2. As A, call `GET /api/analytics/focus-patterns?days=30%26user_id%3D<B's id>` with A's token.
  3. The response contains B's heatmap and series.
- **Fix direction:** In Gin, parse `days` as an integer, clamp it to 7–365, and build the upstream URL with `url.Values`. Python should not trust a free `user_id`; have it verify a signed per-request identity, such as the forwarded user JWT.

### F-02 — Hardcoded fallback secrets
- **Severity:** High (Critical if any fallback is live in production) · **Confidence:** Confirmed in code; production env values need confirmation
- **Location:** `discipline-back/config/config.go:43,47`, `discipline-back/config/seed.go:24`, `discipline-py/app/config.py:25,46`
- **Evidence:**
  ```go
  JWTSecret:      getEnv("JWT_SECRET", "def3013nr2fewfy8923nf…"),            // config.go:43
  AnalyticsAPIKey: getEnv("ANALYTICS_API_KEY", "development_internal_analytics_key"), // config.go:47
  password := getEnv("ADMIN_PASSWORD", "admin123")                             // seed.go:24
  ```
  ```python
  DB_PASSWORD: str = os.getenv("DB_PASSWORD", "zetmax111")                      # config.py:25
  API_KEY: str = os.getenv("ANALYTICS_API_KEY", "devet34tlt_)opment_…")         # config.py:46
  ```
- **What's wrong:** A missing env var silently falls back to a value that is in the source and in GitHub history (`origin git@github.com:zetmax1/…`). The service starts with no warning.
- **Impact:**
  - If `JWT_SECRET` is unset in production, anyone with the source can mint `{"user_id": N, "role": "admin"}` tokens and take over any account.
  - If the admin seed ran without `ADMIN_PASSWORD`, `admin@discipline.app` / `admin123` is a working admin login. Admin can only create more admins, though.
  - If Python's `ANALYTICS_API_KEY` is unset and Gin was configured with the same default, the key is public. F-03 then exposes all users.
  - `zetmax111` is the developer's actual local DB password (verified against the local `.env`; value not reproduced here).
  - The local `.env` values are **not** equal to these defaults (checked without printing them).
- **How to reproduce:** Start the Go service with `JWT_SECRET` unset, sign an HS256 token with the default string, and call `/api/me`.
- **Fix direction:** Fail fast at startup when a required secret is missing or matches a known default. Rotate any secret that may have been deployed with a default, and rotate the DB password that appears in source.

### F-03 — Public analytics service trusts `user_id` and relies on one static key
- **Severity:** High · **Confidence:** Likely (whether the public Railway domain is enabled needs confirmation)
- **Location:** `discipline-py/app/api/analytics_api.py:27-29,45,81,137,173`; `discipline-py/app/smart_schedule/router.py:9-11,22`; `discipline-back/internal/routes/routes.go:79`
- **Evidence:**
  ```python
  def verify_api_key(x_api_key: str = Header(None)):
      if not x_api_key or x_api_key != settings.API_KEY:   # non-constant-time compare
  ...
  user_id: int = Query(..., description="User ID"),
  ```
  ```go
  pythonURL = "https://discipline-py.up.railway.app/"   // public domain as default
  ```
- **What's wrong:** The analytics service is internet-facing (the default upstream is a public `*.up.railway.app` domain, and `/docs` documents every endpoint). One shared static key is the only control, and it grants access to **every** user's data. That includes `/analytics/productivity-trend`, which Gin doesn't even use.
- **Impact:** A key leak, the default key (F-02), or a log or proxy disclosure gives full read access to all users' analytics with no per-user check.
- **How to reproduce:** `curl -H "X-API-Key: <key>" https://<py-host>/analytics/weekly?user_id=<any>`. Do this locally only.
- **Fix direction:** Make Python reachable only over Railway private networking. Verify a per-request signed identity instead of `user_id`. Use `hmac.compare_digest`.

### F-04 — Rate limits bypassable via spoofed `X-Forwarded-For`
- **Severity:** High · **Confidence:** Likely. Gin's behavior is confirmed locally; whether Railway's edge appends to an existing `X-Forwarded-For` header needs confirmation.
- **Location:** `discipline-back/cmd/server/main.go:58`, `discipline-back/internal/middleware/rate_limiter.go:39`
- **Evidence:**
  ```go
  r := gin.Default()        // no SetTrustedProxies → trusts all proxies
  ...
  ip := c.ClientIP()        // rate_limiter.go:39
  ```
  Startup log (`go.log`): `[WARNING] You trusted all proxies, this is NOT safe.`
- **What's wrong:** When every proxy is trusted, Gin returns the **left-most** `X-Forwarded-For` entry, which the client controls. Local test with gin v1.11.0:
  - `XFF="6.6.6.1, 203.0.113.9" → ClientIP=6.6.6.1`
  - `XFF="6.6.6.2, 203.0.113.9" → ClientIP=6.6.6.2`
- **Impact:**
  - Unlimited login attempts. The auth limit of 5/min (`rate_limiter.go:65`) is bypassed, and passwords can be as short as 6 characters (F-23).
  - Unlimited analytics rendering (F-13).
  - Each spoofed IP adds a map entry that lives for 3 minutes, so memory grows without bound.
- **How to reproduce:** Locally, send 20 `POST /api/auth/login` requests, each with a different `X-Forwarded-For` value. None get a 429.
- **Fix direction:** Call `SetTrustedProxies` with Railway's proxy range, or `nil` together with Railway's real-IP header. Add per-account login throttling.

### F-05 — UTC "today" stores blocks and saved plans under the wrong date (UTC+5)
- **Severity:** High · **Confidence:** Confirmed
- **Location:** `discipline/src/hooks/use-tasks.ts:19`, `discipline/src/pages/Planner.tsx:37`, `discipline/src/pages/SmartSchedule.tsx:59-79`, `discipline-back/internal/handlers/task_handler.go:174,301`, `vocab_handler.go:37`; Python `datetime.now()` in `productivity_service.py:31,39`, `weekly_analysis.py:25`, `focus_service.py:34`, `generator.py:21`
- **Evidence:**
  ```ts
  return new Date().toISOString().split('T')[0];          // use-tasks.ts:19 (UTC date)
  date: taskDate.toISOString().split('T')[0]               // SmartSchedule.tsx:79
  ```
  ```go
  date = time.Now().Format("2006-01-02")                   // server clock (alpine image, no TZ → UTC)
  ```
- **What's wrong:** Every "today", week, and month boundary is computed in UTC. Times are stored without a timezone. Dashboard's header uses **local** time (`Dashboard.tsx:44`), so it can disagree with the tasks listed under it.
- **Impact (UTC+5 user, local 00:00–04:59):**
  - A block added in the Planner is saved under **yesterday** and vanishes from "today" at 05:00.
  - Dashboard shows "Tue" but lists Monday's tasks.
  - "Save Weekly Plan" uses local `getDay()` but writes UTC dates, so every saved block lands one calendar day before its labeled weekday.
  - On Monday before 05:00 local, the weekly report still shows the previous week.
  - Weekday-based analytics (heatmap rows, best day) are misattributed for blocks created in that window.
- **How to reproduce:** Set the OS timezone to Asia/Tashkent and the clock to 01:00. Add a block, then inspect `date` in the DB.
- **Fix direction:** Format the local date on the client (not `toISOString`) and send it explicitly. Store the user's IANA timezone and compute day, week, and month boundaries with it on both servers.

### F-06 — "AI detected patterns" and the trend badge can never show data
- **Severity:** Medium · **Confidence:** Confirmed
- **Location:** `discipline/src/pages/Analytics.tsx:98,156`; `discipline-py/app/analytics/pattern_detection.py:41`; `discipline-py/app/services/productivity_service.py:95`
- **Evidence:**
  ```tsx
  const scoreTrend = comparison.focus_score_diff || 0;                  // Python sends "change"
  {focusPatterns?.data?.insights && ...}                                // focus-patterns has no "insights"
  ```
- **What's wrong:**
  - `insights` is produced only by `PatternDetection`, which runs only in `/analytics/productivity-trend`. Gin never proxies that endpoint.
  - The comparison key is `change` (weekly) or `prev_month_focus`/`change` (monthly, inside `analysis`), never `focus_score_diff`.
- **Impact:** The "AI detected patterns" card always says "Not enough data points yet", and the trend badge always shows 0, for every user.
- **How to reproduce:** Log enough completed blocks over several days and open Analytics. The card stays empty.
- **Fix direction:** Define a typed response contract (shared schema or OpenAPI), then either proxy and call the trend endpoint or include `insights` in focus-patterns. Align the comparison key.

### F-07 — "Focus Score" has three different formulas
- **Severity:** Medium · **Confidence:** Confirmed
- **Location:** `discipline/src/pages/Dashboard.tsx:31-38`; `discipline-back/internal/services/task_service.go:122-144`; `discipline-py/app/services/metrics_service.py:92,110-131`
- **Evidence:**
  ```ts
  const focusScore = Math.max(0, Math.round(deepRatio * 100 - distractionPenalty)); // planned hours, all statuses
  ```
  ```python
  score = dw_ratio * 40 + comp_rate * 0.35 + low_distr_bonus * 25   # completed hours only
  ```
- **What's wrong:**

  | Surface | Hours counted | Inputs | Example |
  |---|---|---|---|
  | Dashboard (React) | All planned hours | Deep-work ratio minus a distraction penalty | — |
  | Go `/dashboard/stats` | All planned hours | Same formula as Dashboard (endpoint unused) | — |
  | Python analytics | Completed hours only | Deep ratio, completion, and a *bonus* for few distractions | A day where everything is still pending scores **25**, because the distraction bonus is free when distractions are 0 |

  "Total hours" and "deep work" also mean planned hours on the Dashboard but completed hours in Analytics.
- **Impact:** For the same day, the Dashboard and Analytics show contradictory "Focus Score" and hour values.
- **How to reproduce:** Create two pending deep-work blocks. The Dashboard shows 100; that day in Analytics shows 25.
- **Fix direction:** Pick one definition, implement it in one service, and have the UI read it from there. Remove the unused Go endpoint or route the Dashboard through it.

### F-08 — Schedule generator ignores goals and minutes, crashes on bad input, and claims to learn without data
- **Severity:** Medium · **Confidence:** Confirmed (ran the real generator with a mock DB)
- **Location:** `discipline-py/app/smart_schedule/generator.py:46-55,62-76,88-90,121`; `discipline-py/app/smart_schedule/schemas.py:11-21`
- **Evidence:**
  ```python
  defaults = {'deep-work': 9, 'study': 14, 'rest': 19}            # :50, always fills _learned_patterns
  if len(self._learned_patterns) == 0:                              # :62, never true
  daily_deep_work = max(1, int(request.goals.deepWorkHours // 5))   # :69
  return int(time_str.split(":")[0])                                # :55, drops minutes
  ```
- **Observed results:**

  | Input | Result |
  |---|---|
  | UI defaults, goals 15/10/7 | Places 15/**12**/7. Study gets weekend extras. |
  | Goals 0/0/0 or −50/−5/−1 | Still places 5/5/7 hours |
  | Goals 4/4/6 | Places 5/5/7 |
  | Goals 1000 | Silently truncated, no warning in the reasoning |
  | No history | Reasoning still says "Learned your historical preferences" and "AI insight … based on your past focus peaks" |
  | Meeting 09:00–09:45 | Deep work placed at **09:00–10:00**, overlapping it. Gym 17:00–18:30 likewise only blocks 17:00. |
  | Start time `""` or `"9am"` | `ValueError` → 500 → Gin returns a generic 500 |
  | `deepWorkHours=Infinity` | 500 |
  | History of 08:00 and 20:00 deep work | Integer mean picks **14:00** |
  | Same inputs twice | Output is deterministic apart from UUIDs |
  | Rest preference wrapping past midnight | Can be placed at 00:00–05:00. Saved blocks there are invisible in the Planner, which only renders 06–24 (`Planner.tsx:13`). |

  The only history used is the mean start hour of completed tasks per category over the last 30 days (`generator.py:20-51`).
- **Impact:** Users get plans that don't match their stated goals, collide with commitments, and are presented as AI-learned when they aren't.
- **How to reproduce:** Run the generator with the UI default commitments and goals 0/0/0 (as in the experiment above) and compare the placed hours.
- **Fix direction:** Validate inputs in Pydantic (an `HH:MM` regex, goals between 0 and 168). Work in minutes. Distribute exact goal hours and report shortfalls. Only claim learning when history exists.

### F-09 — User-added commitments always apply to Monday only
- **Severity:** Medium · **Confidence:** Confirmed
- **Location:** `discipline/src/pages/SmartSchedule.tsx:28,36,107`
- **Evidence:**
  ```tsx
  const [selectedDay, setSelectedDay] = useState('Monday');   // setSelectedDay is never called
  ... days: [selectedDay] }]);                                // every new commitment → ['Monday']
  <span>{c.startTime}–{c.endTime}</span>                       // days are never displayed
  ```
- **Impact:** A commitment the user adds (for example, a daily job 09:00–17:00) blocks only Monday. The rest of the week gets deep work scheduled on top of it, and the user can't see why.
- **How to reproduce:** Add "Work 09:00–17:00", then generate. Tuesday through Sunday have deep work inside 09–17.
- **Fix direction:** Add a day multi-select, show the days in the list, and validate `days` against an enum server-side.

### F-10 — No server-side validation of task times, dates, overlaps, or update fields
- **Severity:** Medium · **Confidence:** Confirmed
- **Location:** `discipline-back/internal/handlers/task_handler.go:30-33,37-44`; `discipline-back/internal/services/task_service.go:74-97,157-167`
- **Evidence:**
  ```go
  StartTime string `json:"startTime" binding:"required"`      // no format check
  Date      string `json:"date" binding:"required"`           // no format check
  Status       *string `json:"status,omitempty"`               // update: no oneof
  Distractions *int    `json:"distractions,omitempty"`         // update: no bounds
  Energy       *int    `json:"energy,omitempty"`               // update: no 1-5 check
  return float64(eh*60+em-sh*60-sm) / 60                       // negative when end < start
  ```
- **What's wrong:**
  - The API accepts end ≤ start, overlapping blocks, any date string, any status or category on update, negative distractions, and energy of 999.
  - Only the Planner UI enforces end > start (`Planner.tsx:45`).
  - Create validates `category` with `oneof` (`:29`), but update doesn't.
- **Impact (on the user's own data):**
  - **Go focus score can exceed 100.** A deep-work block 09:00–12:00 plus an admin block 12:00–10:00 gives ratio 3 → score 300. Total hours go negative.
  - Python clamps such durations to 0 (`task.py:33`), and a completed zero-length task crashes Analytics (F-11).
  - A malformed date inside the queried range makes `pd.to_datetime` raise, which turns focus-patterns into a 500.
  - An unknown category renders an empty badge and an `undefined` CSS class.
- **How to reproduce:** `PUT /api/tasks/:id {"endTime":"08:00","status":"lol","energy":999}` returns 200.
- **Fix direction:** Validate `HH:MM` and `YYYY-MM-DD` formats, end > start, enums, and bounds on both create and update. Reject overlaps per (user, date) in a transaction.

### F-11 — Any completed zero-duration task makes the Analytics page return 500
- **Severity:** Medium · **Confidence:** Confirmed (matplotlib 3.9.2 raises `ValueError: cannot convert float NaN to integer` for all-zero wedges)
- **Location:** `discipline-py/app/visualization/charts.py:173`; called from `analytics_api.py:62,111`
- **Evidence:**
  ```python
  wedges, texts, autotexts = ax.pie(sizes, labels=labels, ... autopct="%1.1f%%", ...)
  ```
- **What's wrong:** The category distribution is non-empty but sums to 0 when every completed task in the period has 0 duration. That happens with start == end, an inverted range, or an overnight block (all possible via the API; F-10). The pie call then raises, and the figure is never closed.
- **Impact:** `/api/analytics` returns 500 for that user for the rest of the week or month, so the whole Analytics page shows an error. Each failed request also leaks a figure in pyplot's global registry.
- **How to reproduce:** Locally, create a deep-work block 10:00–10:00, mark it completed, then open Analytics.
- **Fix direction:** Skip the chart when the total is 0. Close figures in `try/finally`.

### F-12 — Heatmap color scale and hour bucketing are wrong
- **Severity:** Medium · **Confidence:** Confirmed (reproduced the colors)
- **Location:** `discipline-py/app/visualization/focus_heatmap.py:44-56`; `discipline-py/app/services/focus_service.py:63,84-87`
- **Evidence:**
  ```python
  sns.heatmap(matrix, ax=ax, cmap="YlOrRd", ...)                     # no vmin/vmax
  for h in range(max(sh, 6), min(eh + 1, 24)):                       # end hour inclusive
      matrix[wd][idx] += row["duration_hours"] / max(eh - sh + 1, 1)
  ```
- **What's wrong:**
  1. With all-zero data, matplotlib expands the singular range to **−0.1…0.1**, and 0 maps to the colormap midpoint. Measured cell color is `(0.992, 0.549, 0.234)`, identical to `cmap(0.5)` (orange). An empty week looks moderately active.
  2. The end hour is counted: a 09:00–10:00 block is split 0.5/0.5 into the 09 and 10 cells. Minutes are ignored, so 09:45–10:15 is spread over 09 and 10 as if it covered two hours.
  3. Overnight blocks (sh > eh) get `range()` empty and duration 0, so they are dropped. Hours 00–05 are never shown.
- **Impact:** Users see activity that didn't happen, and real activity shows up in the wrong hour.
- **How to reproduce:** Open focus-patterns for a user with no completed deep work and compare the heatmap colors against the empty data.
- **Fix direction:** Set `vmin=0` and a `vmax` of at least a small positive value. Bucket by minute overlap with `[h, h+1)`. Handle a wrap past midnight by splitting the block.

### F-13 — pyplot used from FastAPI's threadpool; unbounded CPU-heavy rendering
- **Severity:** Medium · **Confidence:** Likely
- **Location:** `discipline-py/app/api/analytics_api.py:44,80,172` (sync `def` endpoints); `discipline-py/app/visualization/charts.py:24,38-44`; `focus_heatmap.py:42`
- **Evidence:**
  ```python
  @router.get("/focus-patterns")
  def get_focus_patterns(...):          # sync → Starlette runs it in a threadpool (default 40 threads)
      chart_heatmap = focus_heatmap(...) # plt.subplots / plt.close, global pyplot state
  ```
- **Each part of the suspicion:**

  | Suspicion | Verdict |
  |---|---|
  | Agg backend not set | Not an issue: it's set |
  | Blocking inside `async def` | Not an issue: the endpoints are sync |
  | Figures never closed | Not an issue on the success path |
  | Thread safety | **Issue.** `pyplot` (`plt.subplots`, `plt.close`, `sns.set_theme`) uses global state and is documented as not thread-safe. Concurrent requests share it. |
  | Figure leaks | **Issue.** Figures leak on exceptions (F-11). |

  One Analytics page load renders 7 PNGs at 150 dpi (3 or 4 for week/month plus 4 for focus-patterns) on a single uvicorn worker. Python has no rate limit of its own, and Gin's limit is bypassable (F-04).
- **Impact:** Possible garbled or crossed charts under concurrency, memory growth, and easy CPU exhaustion of the analytics service.
- **How to reproduce:** Locally, fire 20 concurrent focus-patterns requests and watch CPU, response latency, and the pyplot figure count.
- **Fix direction:** Use the object-oriented API (`matplotlib.figure.Figure`) instead of pyplot. Cache charts per user and day. Cap concurrency for rendering. Consider rendering on the client, since Recharts is already used.

### F-14 — No vocabulary job: gaps, duplicates, permanent fallback text, unvalidated date
- **Severity:** Medium · **Confidence:** Confirmed
- **Location:** `discipline-back/internal/services/vocab_service.go:34-72,174-183,209-224`; `discipline-back/internal/models/vocabulary.go:8,15`; `discipline-back/internal/handlers/vocab_handler.go:35-38`
- **Evidence:**
  ```go
  if !hasEnglish || !hasRussian {                      // :53 runs only when a user GETs /vocabulary/today
      newWords := s.fetchDailyWords(userID, date)
      ...
      if err := s.vocabRepo.Create(&newWords[i]); err != nil {
          log.Printf("Failed to save vocab word: %v", err)   // :64 swallowed
  ```
  ```go
  Definition: "An advanced English vocabulary word",   // :180 fallback stored permanently
  ```
- **What's wrong:**
  - **There is no scheduled job.** Words are created only when the logged-in user loads the Dashboard or Vocabulary page. The date gaps (2026-07-11 → 2026-08-11 → 2026-10-28) are exactly the days the user didn't open the app, so nothing was "lost on redeploy".
  - There is no unique key on (user_id, date, language). Two tabs, two devices, or 2+ instances racing during the dictionary call (up to 5s) produce duplicate rows.
  - If the dictionary API is down, the placeholder definition is stored and never retried, because the language now counts as present.
  - The `?date=` parameter is unvalidated, so a client can create rows and trigger outbound calls for arbitrary dates.
  - `io.ReadAll` on the dictionary response is unbounded (`:224`). The timeout of 5s is fine.
- **Impact:** Missing history, duplicate cards, and permanently bad entries.
- **How to reproduce:** Locally, send two concurrent `GET /api/vocabulary/today` requests for a user with no words today and count the rows.
- **Fix direction:** Add a unique index on (user_id, date, language) with upsert. Validate `date`. Don't persist the fallback (or mark it for retry). Use `io.LimitReader`. If a daily cadence is really wanted, generate words with an external cron (Railway cron) rather than in-process.

### F-15 — Wrong dictionary sense and part of speech; CEFR labels hardcoded
- **Severity:** Medium · **Confidence:** Confirmed (checked the live dictionary response)
- **Location:** `discipline-back/internal/services/vocab_service.go:153-162,248-257`; `discipline/src/pages/Vocabulary.tsx:64`
- **Evidence:**
  ```go
  meaning := entry.Meanings[0]                          // first part of speech
  def.Definition = meaning.Definitions[0].Definition    // first (often archaic) sense
  ```
  ```tsx
  {word.language === 'russian' ? 'Russian A2+' : 'English C1'}
  ```
- **What's wrong:**
  - For `compelling`, the API returns meanings in the order *verb* ("To drive together, round up"; 7 senses), *noun*, *adjective* ("Strongly or irresistibly evoking interest…"). The code always takes `meanings[0].definitions[0]`.
  - **There is no CEFR data anywhere.** The list is a hardcoded array of 30 English words and 30 Russian entries. The level badge is a UI constant.
  - External text isn't length-limited. It's rendered as React text, so there is no XSS risk.
  - Word choice is `hash(date) % 30`, so every user gets the same word each day and words repeat often.
- **Impact:** Learners are taught an archaic verb sense for a word they will meet as an adjective, and the level badge is not backed by any data.
- **How to reproduce:** Request today's words on a date that hashes to "compelling" and compare the stored definition with the adjective sense.
- **Fix direction:** Store the intended part of speech with each pool word and choose the matching meaning. Store a real level field. Truncate fields.

### F-16 — Future-dated tasks deflate weekly completion and zero the streak
- **Severity:** Medium · **Confidence:** Confirmed by code
- **Location:** `discipline-py/app/analytics/weekly_analysis.py:43-50`; `discipline-py/app/services/productivity_service.py:57-58`
- **Evidence:**
  ```python
  sorted_daily = sorted(daily, key=lambda x: x["date"], reverse=True)   # starts from Sunday
  for day in sorted_daily:
      if day["completion_rate"] >= 70: streak += 1
      else: break
  ```
- **What's wrong:** The week range is Monday–Sunday, including future days. "Save Weekly Plan" creates pending tasks for the next 7 days (`SmartSchedule.tsx:83`).
- **Impact:** After saving a plan:
  - Weekly completion counts not-yet-due tasks as incomplete.
  - The streak is always 0.
  - "Worst day" is a future day.
- **How to reproduce:** Save a weekly plan, complete all of today's tasks, and open Analytics. The streak is 0.
- **Fix direction:** Clamp the end of every range to "today" in the user's timezone.

### F-17 — No timeouts or body limits; unbounded, non-transactional bulk insert
- **Severity:** Medium · **Confidence:** Confirmed
- **Location:**
  - `discipline-back/internal/handlers/analytics_handler.go:65,79,112,125,159,167,180`
  - `discipline-back/internal/handlers/task_handler.go:50`
  - `discipline-back/internal/services/task_service.go:46-54`
  - `cmd/server/main.go:66` (`r.Run`: no server read/write timeouts)
- **Evidence:**
  ```go
  client := &http.Client{}                                   // no timeout
  req, err := http.NewRequest("POST", endpoint, c.Request.Body) // unbounded body streamed upstream
  Tasks []CreateTaskRequest `json:"tasks" binding:"required,dive"` // no max length
  for _, task := range tasks { if err := s.taskRepo.Create(task); err != nil { return err } } // no tx
  ```
- **Impact:**
  - A slow or hung Python service ties up Gin goroutines indefinitely.
  - One `/tasks/bulk` request with 100k items does 100k sequential INSERTs.
  - A failure midway leaves a partial plan.
  - There is no request size cap anywhere.
- **How to reproduce:** Locally, POST 100k items to `/api/tasks/bulk` and watch the insert count and latency. Kill Python mid-request and watch the analytics request hang.
- **Fix direction:**
  - Use a shared `http.Client` with a timeout and the request context.
  - Wrap bodies in `http.MaxBytesReader` and responses in `io.LimitReader`.
  - Cap bulk size (for example, 200) and use `CreateInBatches` inside a transaction.
  - Configure `http.Server` timeouts.

### F-18 — 72h JWT in localStorage with no revocation
- **Severity:** Low · **Confidence:** Confirmed
- **Location:** `discipline/src/lib/api.ts:7-12,143-148`; `discipline-back/internal/services/auth_service.go:148-157`; `discipline-back/config/config.go:32`
- **Evidence:**
  ```ts
  localStorage.setItem('auth_token', token);
  export function logout() { removeToken(); ... }   // client-side only
  ```
- **What's wrong:**
  - Tokens live for 72h with no refresh flow. Logout and password change don't invalidate existing tokens (there is no `jti` or token version).
  - The algorithm is properly pinned to HMAC (`auth_middleware.go:38`), and expiry is enforced by jwt/v5.
  - No XSS sink was found: React escapes output, and the only `dangerouslySetInnerHTML` is the shadcn chart with static config. There is no CSP header, though.
- **Impact:** A stolen token stays valid for up to 3 days, even after the victim changes their password.
- **How to reproduce:** Log in, copy the token, log out (or change the password), and call `/api/me` with the copied token. It still works.
- **Fix direction:** Shorter access tokens with refresh, a per-user token version checked in the middleware, and a CSP.

### F-19 — 50 plaintext credentials committed
- **Severity:** Medium · **Confidence:** Confirmed in git; whether these accounts exist in production needs confirmation
- **Location:** `discipline-back/fake_users_credentials.csv` (tracked; added in commit "feat: Add analytics proxy endpoints … include fake user credentials")
- **Evidence:** Header is `Name,Email,Password,Role`, followed by 50 rows of email/password pairs. Values are not reproduced here.
- **Also tracked in git:** a 48 MB compiled binary `discipline-backend` and `arms_cache/` (Alibaba Cloud ARMS APM config with app and region IDs).
- **Impact:** If these accounts were seeded into production, anyone who can read the repo can log in as them.
- **How to reproduce:** `git ls-files | grep fake_users_credentials.csv`.
- **Fix direction:** Delete the accounts or rotate their passwords in every environment. Remove the files from the repo and purge them from history if it's public.

### F-20 — Postgres connection forces `sslmode=disable`
- **Severity:** Medium · **Confidence:** Needs confirmation (depends on whether production `DB_HOST` is a private or public endpoint)
- **Location:** `discipline-back/config/database.go:16`
- **Evidence:** `"host=%s port=%s user=%s password=%s dbname=%s sslmode=disable"`
- **Impact:** If the database is reached through Railway's public TCP proxy, credentials and all user data cross the internet unencrypted. Python's URL has no `sslmode`, so libpq's default `prefer` applies there.
- **How to reproduce:** Check the production `DB_HOST`. If it's a public proxy hostname, the connection runs over the internet without TLS.
- **Fix direction:** Make `sslmode` configurable and default it to `require` for non-private hosts.

### F-21 — CORS reflects every Origin; Python uses `*` with credentials
- **Severity:** Low · **Confidence:** Confirmed
- **Location:** `discipline-back/internal/middleware/cors_middleware.go:25-27`; `discipline-py/main.py:23-29`; `discipline-py/app/config.py:42`
- **Evidence:**
  ```go
  if origin != "" {
      // Always reflect the origin back ...
      c.Writer.Header().Set("Access-Control-Allow-Origin", origin)
  ```
- **What's wrong:** `ALLOWED_ORIGINS` is effectively unused. It's Low because auth uses an `Authorization` header read from localStorage, not cookies, and Go doesn't send `Allow-Credentials`. A foreign site can't attach the token.
- **Impact:** Today, none directly. It becomes exploitable if the app ever moves to cookie-based auth.
- **How to reproduce:** Send any request with `Origin: https://evil.example` and observe it echoed in `Access-Control-Allow-Origin`.
- **Fix direction:** Use the parsed allowlist. Remove `"*"` from Python, which shouldn't be called from browsers at all.

### F-22 — Public API docs; Gin debug mode by default
- **Severity:** Low · **Confidence:** Confirmed in code; production `GIN_MODE` needs confirmation
- **Location:** `discipline-back/internal/routes/routes.go:38`; `discipline-back/cmd/server/main.go:58` (no `SetMode`; the local `go.log` shows `Running in "debug" mode`); `discipline-py/main.py:15` (`/docs` and `/openapi.json` enabled), `main.py:53` (`reload=True` only for `python main.py`, not the Procfile)
- **Impact:** Full attack-surface documentation for both services is public, including Python's `user_id` endpoints. GORM's default logger writes SQL with literal values (for example, user emails on failed logins) to logs.
- **How to reproduce:** Open `/swagger/index.html` on the Go service or `/docs` on the Python service. No login is required.
- **Fix direction:** Gate docs behind an env flag, set `GIN_MODE=release`, and set the GORM logger to Warn or Silent.

### F-23 — User enumeration on register; weak password rules
- **Severity:** Low · **Confidence:** Confirmed
- **Location:** `discipline-back/internal/services/auth_service.go:51-53,84-91,126-137`; `discipline-back/internal/handlers/auth_handler.go:28,80`
- **Evidence:**
  ```go
  return nil, "", errors.New("user with this email already exists")   // 409 on register
  Password string `json:"password" binding:"required,min=6"`
  ```
- **What's wrong:**
  - Login messages are uniform, but register returns a distinct 409, and a login for an unknown email skips bcrypt (timing difference).
  - A new password on profile update has **no** minimum length.
  - Passwords over 72 bytes make bcrypt fail with "failed to hash password", which comes back as a 409.
- **Impact:** Attackers can tell which emails are registered, and users can set trivially weak passwords. Combined with F-04, that makes brute force cheap.
- **How to reproduce:** Register an email that already exists and get a 409 naming the conflict. Change a password to `"1"` through `PUT /api/me` and get a 200.
- **Fix direction:** Use a generic register response, enforce the same password policy on change, and cap length at 72 bytes.

### F-24 — Email change needs no password and no format validation
- **Severity:** Low · **Confidence:** Confirmed
- **Location:** `discipline-back/internal/handlers/auth_handler.go:200-205`; `discipline-back/internal/services/auth_service.go:118-124`
- **Evidence:** `Email string json:"email,omitempty"` has no `binding:"email"`, and `user.Email = email` runs without checking the current password.
- **Impact:** Anyone holding a session (F-18) can change the login email, and the account can end up with an invalid email such as `"x"`. `Name` has no length limit on update either.
- **How to reproduce:** `PUT /api/me {"email":"x"}` with a valid token returns 200, and the account's email is now `x`.
- **Fix direction:** Validate the format and require the current password to change the email.

### F-25 — Unpinned base images; container runs as root
- **Severity:** Low · **Confidence:** Confirmed
- **Location:** `discipline-back/Dockerfile:1,16,25`
- **Evidence:** `FROM golang:alpine AS builder` / `FROM alpine:latest` / no `USER`
- **Impact:** Builds aren't reproducible, so the Go toolchain version (and its stdlib CVEs, F-26) changes silently between deploys. The process runs as root.
- **How to reproduce:** Build the image twice some time apart and compare the Go versions. Inside the container, `id` reports uid 0.
- **Fix direction:** Pin by version and digest, and add a non-root `USER`. A distroless static image would also work.

### F-26 — Dependency CVEs
- **Severity:** Low · **Confidence:** Confirmed (tool output; reachability triaged below)
- **Go (govulncheck, 17 called):**
  - Stdlib (net/http, html/template, crypto/tls and x509) at local go1.26.8; fixed in 1.26.9/1.26.10. What production gets depends on the unpinned `golang:alpine` image (F-25).
  - `golang.org/x/net` v0.51.0: HTTP/2 issues. Gin serves HTTP/1.1 without h2c, so this is client-side only.
  - `x/text` v0.34.0: hit only through GORM init paths, not with user input.
  - `pgx/v5` v5.8.0 (GO-2026-5004, SQL injection via dollar-quoted literals): GORM sends parameterized queries with no dollar-quoted SQL, so **not reachable**.
  - `quic-go`: HTTP/3 is not used.
- **Python (pip-audit):**
  - `starlette 0.38.6` has 7 advisories (multipart/form DoS, Host/path URL reconstruction, HTTPEndpoint, Windows StaticFiles). **None are reachable**: there are no form endpoints, no HTTPEndpoint, no StaticFiles, and `request.url` isn't used for security decisions.
  - `python-dotenv 1.0.1`: `set_key` is not used.
- **npm (32: 2 critical, 22 high, 7 moderate, 1 low):**
  - Reachable at runtime: `serve` 14.2.5 → `compression` (<1.8.2, memory leak on aborted responses) on the production static server, which is Low. `react-router` 6.30.1 open-redirect advisories need attacker-controlled redirect targets, and the app only navigates to fixed paths, so they are not reachable.
  - Everything else (vitest/tinypool "critical", vite, rollup, postcss, glob, and others) is **dev/build-time only**.
- **Impact:** Today, low, because no high-impact path is reachable. The real risk is drift: the unpinned build images and stale lockfiles mean new CVEs land in production unnoticed.
- **How to reproduce:** Run `govulncheck ./...`, `pip-audit`, and `npm audit` (see §6).
- **Fix direction:** Upgrade pgx, x/net, and x/text. Bump Starlette with FastAPI. Run `npm audit fix` for `serve`, `react-router-dom`, and `vite`. Pin the Go toolchain.

### F-27 — Frontend: lost distraction updates, stale error, demo-mode redirect loop
- **Severity:** Low · **Confidence:** Confirmed
- **Location:** `discipline/src/pages/Planner.tsx:190-194`; `discipline/src/pages/Login.tsx:36`; `discipline/src/pages/Analytics.tsx:20-22`; `discipline/src/lib/api.ts:68-74` with `App.tsx:42`
- **Evidence:**
  ```tsx
  updateTask(task.id, { distractions: task.distractions + 1 })   // absolute value from the last fetch
  toast.error(error || 'Authentication failed');                   // `error` is the render-time value
  ```
- **What's wrong:**
  - Several fast "+" clicks before a refetch send the same absolute value, so increments are lost. Concurrent updates also overwrite each other because the server uses a full-row `Save()`.
  - The login error toast shows the previous error, or the generic text, instead of the current one.
  - `useEffect` is missing a dependency (`loadData`) per eslint `exhaustive-deps`.
  - In demo mode, opening Analytics or Smart Schedule hits the API without a token. The 401 handler hard-redirects to `/login`, which immediately redirects to `/`, so those pages are unusable and the redirect gives no explanation.
- **Impact:** Undercounted distractions, misleading login messages, and broken pages in demo mode.
- **How to reproduce:** Click "+" five times quickly on a pending block and count the stored distractions. In demo mode, open Analytics and you land back on the Dashboard.
- **Fix direction:** Send increments, or do optimistic updates via `setQueryData`. Read the error from the caught exception. Disable API-backed pages in demo mode.

### F-28 — String-typed times and dates, missing indexes and FK, masked DB errors, pool defaults
- **Severity:** Low · **Confidence:** Confirmed
- **Location:** `discipline-back/internal/models/task.go:24-32`; `discipline-back/internal/repositories/task_repository.go:61-65`; `discipline-back/config/database.go:20-28`; `discipline-py/app/database.py:13-14`
- **Evidence:**
  ```go
  result := r.db.Where("id = ? AND user_id = ?", id, userID).Delete(&models.Task{})
  if result.RowsAffected == 0 { return gorm.ErrRecordNotFound }   // DB error reported as 404
  ```
- **What's wrong:**
  - Times and dates are `varchar`. Ordering and range filters are lexical, so `"9:00"` sorts after `"10:00"` and a malformed date can match a range (F-10).
  - Indexes are separate on `user_id` and `date`; every hot query filters on both, so a composite index is missing.
  - There is no FK or `ON DELETE` from `tasks`/`vocabulary_words` to `users`.
  - Schema changes rely on `AutoMigrate` with no versioned migrations.
  - The Go `sql.DB` pool uses defaults (unbounded open connections). Python's pool is 5+10 against 40 threadpool workers.
- **Impact:** Wrong sort order for non-padded times, slower queries as data grows, orphaned rows, and DB errors surfacing as misleading 404s.
- **How to reproduce:** Create tasks at `9:00` and `10:00` via the API, then list them. The 10:00 task sorts first.
- **Fix direction:** Use `time`/`date` column types (or validate formats strictly), add an index on (user_id, date), add FKs, adopt migrations, and set pool limits.

### F-29 — Commitments and goals not persisted; "Save Weekly Plan" not idempotent
- **Severity:** Low · **Confidence:** Confirmed
- **Location:** `discipline/src/pages/SmartSchedule.tsx:18-23,53-91`
- **Evidence:** Commitments and goals live in `useState` and reset to the defaults on reload. Save calls `POST /tasks/bulk` with no dedupe key.
- **Impact:**
  - Saving after a regeneration duplicates every block.
  - Days are mapped to "next occurrence from tomorrow", so a saved "week" straddles two calendar weeks. For example, saved on a Wednesday, the Monday and Tuesday blocks land next week.
- **How to reproduce:** Generate and save, then generate and save again. Every block appears twice in the Planner.
- **Fix direction:** Persist commitments and goals server-side. Save against an explicit target week and replace that week's generated blocks.

---

## 5. Known suspicions 1–12

| # | Verdict | Evidence and notes |
|---|---|---|
| 1 | **Confirmed (different cause)** | Commitments do have `days` (`schemas.py:13`, default UI data). But **user-added** commitments always get `days: ['Monday']` because `setSelectedDay` is never called, and days are never displayed (`SmartSchedule.tsx:28,36,107`). See F-09. An overnight commitment on day D blocks D's 00:00–06:59 rather than D+1's (`generator.py:88-90`). That's harmless with all 7 days, but wrong for a weekday-only sleep entry. |
| 2 | **Confirmed (partially)** | The generator handles the wrap for occupancy at hour granularity (`generator.py:88-90`). Elsewhere it's mishandled: Python `duration_hours` clamps to 0 (`task.py:33`); Go and Dashboard return **negative** hours (`task_service.go:167`, `Dashboard.tsx:15-19`); the heatmap drops overnight blocks (`focus_service.py:84`). The Planner UI can't create such blocks (end ≤ 24:00, `Planner.tsx:45`), but the API accepts them (F-10). |
| 3 | **Partially not an issue** | The UI **does** collect distractions with a ± counter in the Planner, visible only while a block is pending (`Planner.tsx:187-198`). The Dashboard doesn't show it. Division by zero is guarded (`metrics_service.py:127`, `task_service.go:140`); no NaN or inf found. Real issue: with 0 distractions, Python adds a free +25, so a day with only pending tasks scores 25 (F-07). |
| 4 | **Confirmed (vmin/vmax); mixed on the rest** | All-zero data → colorbar −0.1…0.1, cells mid-orange (measured). See F-12. Agg backend is set ✔. Figures are closed on success ✔ but leak on exceptions (F-11). pyplot from a threadpool is not thread-safe (F-13). No blocking in `async def`, because the routes are sync ✔. |
| 5 | **Confirmed (different cause)** | There is **no job**. Words are created lazily on `GET /vocabulary/today`, so gaps are days the app wasn't opened. Errors are swallowed and the fallback is stored permanently with no retry. No unique constraint → duplicates under concurrency or multiple instances. Timeout is 5s ✔; body read is unbounded. See F-14. |
| 6 | **Confirmed** | Uses `entries[0].meanings[0].definitions[0]`. The live API lists the *verb* sense "To drive together, round up" first for "compelling". There is no CEFR source; the badge is hardcoded in the UI (`Vocabulary.tsx:64`). External text is unvalidated and unlimited in length, but rendered safely. See F-15. |
| 7 | **Confirmed (hardcoded); enums consistent** | Category strings are defined separately in Go (`models/task.go:7-11`, `task_handler.go:29` `oneof`), TS (`types.ts:1`, `CATEGORY_LABELS`), Python (`generator.py:33` patterns, `charts.py` `COLORS`, `focus_service.py`). Spelling is consistent (`deep-work`, `study`, `admin`, `gym`, `rest`). Goals intentionally have only 3 fields (`schemas.py:15-18`); "Gym" is modeled as a fixed commitment. The update path doesn't validate category (F-10). |
| 8 | **Not an issue (data); cosmetic (UI)** | `<input type="time">` always yields a 24h `"HH:mm"` value; only the browser's picker is locale-formatted (12h in en-US). The list prints raw strings (`SmartSchedule.tsx:107`). Times are stored as unvalidated `varchar` everywhere (F-28). A cleared input sends `""`, which causes a Python 500 (F-08). |
| 9 | **Confirmed** | `toISOString()` (UTC) on the client and `time.Now()`/`datetime.now()` (UTC server) everywhere. Wrong dates for UTC+5 between 00:00 and 04:59; saved plans are off by one. See F-05. No `new Date("YYYY-MM-DD")` parsing was found; the bug is the opposite direction (local → UTC string). |
| 10 | **Confirmed** | The API rejects none of: overlaps, end ≤ start, out-of-range energy on update (create validates 1–5), bad status or category on update. See F-10. |
| 11 | **Confirmed** | Goals 0 or negative → still 5h/5h/7h; huge → silently truncated; goals not met exactly (15/10/7 → 15/12/7); no commitments → works; deterministic apart from UUIDs. It does use history: the mean start hour of completed tasks over the last 30 days. But it always claims to have learned, even with none. See F-08. |
| 12 | **Confirmed** | Completion, total hours, deep work, and focus score are computed in React (Dashboard), Go (`/dashboard/stats`, unused), and Python, with different inputs (planned vs completed) and different focus formulas. See F-07. |

---

## 6. Tool summary

| Tool | Ran? | Result | Triage |
|---|---|---|---|
| `go build ./...` | ✔ | OK | — |
| `go vet ./...` | ✔ | 0 issues | — |
| `staticcheck ./...` | ✔ (installed to scratch) | 0 issues | — |
| `gosec ./...` | ✔ | 4 × G404 (math/rand) at `vocab_service.go:272`, `quote_handler.go:31,103,110` | **False positives.** Used for word and quote selection, not security. |
| `govulncheck ./...` | ✔ | 17 called vulnerabilities (stdlib, x/net, x/text, quic-go, pgx) | → F-26. pgx SQLi and HTTP/2 server issues are not reachable. |
| `go test -race ./...` | ✔ | **No test files** in any package | No coverage for auth, IDOR, or validation. |
| `ruff check` | ✔ | 92 findings (16 F401 unused imports, 4 F841, 3 B023, 5 B008, style rules) | B008 (`Depends`) and B023 (`place_block` closure called in the same iteration) are **false positives**. The rest is quality only. |
| `mypy` | ✔ | 17 errors | All typing noise from pandas/dict `object` inference and a false positive on `ax.pie` unpacking. No real bugs. |
| `bandit -r` | ✔ | 1 Medium: B104 bind 0.0.0.0 (`config.py:37`) | **False positive** (container requirement). It missed the hardcoded secrets because they're `getenv` defaults, which manual review caught (F-02). |
| `pip-audit` | ✔ (on an exact-pin venv; `-r` mode failed on ensurepip) | 28 entries across starlette, python-dotenv, and pip | pip is the scratch tooling venv, not production. The rest is not reachable (F-26). |
| `pytest` | ✔ | 2 passed (`tests/test_smart_schedule.py`) | Tests don't cover goals ≤ 0, minutes, or bad input. `test_monthly.py` is a broken script: it `await`s a sync function. |
| `npm audit` | ✔ | 32 (2 critical, 22 high, 7 moderate, 1 low) | Almost all dev or build only. Runtime: `serve`/`compression` (Low). See F-26. |
| `npx eslint .` | ✔ | 15 errors, 8 warnings | 12 × `no-explicit-any`, 7 × `only-export-components` (shadcn), 1 × `exhaustive-deps` (`Analytics.tsx:22`, F-27). |
| `npm run build` (as `vite build --outDir <scratch>`) | ✔ | OK; 860 KB JS chunk | **No source maps emitted.** Only `VITE_API_URL` is read from env; no secrets in the bundle. |
| `npx tsc --noEmit` | ✔ | 0 errors | — |
| `vitest run` | ✔ | 1 placeholder test passed | — |
| `gitleaks detect` | ✘ not installed | — | Replaced with a manual regex scan of the full `git log -p --all` for all three repos. Only hit: README placeholders (`JWT_SECRET=you…`), a **false positive**. Committed secrets are the in-code defaults (F-02) and the CSV (F-19). The frontend `.env` was committed and later removed; it contained only `VITE_API_URL`, which is not secret. |

Working-tree note: `git -c core.fileMode=false status` shows the only content change is in `discipline/vite.config.ts` (port 8080 → 8081). Every other "M" is a file-mode change (all files are 0755).

---

## 7. What was not checked, and why

- **Production configuration and behavior.** Railway env vars, `GIN_MODE`, whether the Python service's public domain is enabled, whether Railway's edge appends to or overwrites `X-Forwarded-For`, and the database host or network. The brief forbids touching production. This affects the confidence of F-02, F-03, F-04, F-20, and F-22.
- **GitHub repo visibility.** `gh` is not installed. If the repos are public, F-02 and F-19 become more severe.
- **Live database contents.** Whether the 50 CSV accounts or the default admin exist in production, and how many duplicate vocabulary rows exist.
- **Runtime load testing.** No load testing of the matplotlib concurrency issue (F-13) or memory growth; it's assessed from code and documented pyplot semantics.
- **The frontend in a real browser.** No E2E tests exist. UI conclusions come from reading the code.
- **`notebooks/exploration.ipynb`.** The file is empty or invalid JSON, so ruff couldn't parse it.
- **`docs/` (swagger).** Generated files; reviewed only for exposure, not content accuracy.

---

## 8. Prioritized fix order

**Fix before any new features**
1. F-01: validate and encode `days` in the Gin proxy, and stop trusting a bare `user_id` in Python.
2. F-02: fail fast on missing or default secrets. Rotate `JWT_SECRET`, `ANALYTICS_API_KEY`, the admin password, and the DB password if a default was ever live.
3. F-03: put Python on private networking only, verify per-request identity, use a constant-time key compare, and disable `/docs`.
4. F-04: configure trusted proxies and add per-account login throttling.
5. F-19: remove or rotate the CSV accounts and remove the committed binary and APM cache.
6. F-05: client-local dates plus a per-user timezone on the server.

**Fix soon**
- F-10 and F-17: server-side validation, body and bulk limits, HTTP timeouts, transactional bulk insert.
- F-11, F-12, F-13: chart crash, heatmap scale and buckets, pyplot thread safety, render caching.
- F-06, F-07, F-16: analytics contract, a single focus-score definition, clamping ranges to today.
- F-08, F-09: generator input validation, minute precision, honest reasoning, commitment day picker.
- F-14, F-15: vocabulary unique key, no persisted fallback, correct sense selection, real level data.
- F-20, F-18: DB TLS; shorter tokens with revocation and a CSP.

**Fix later**
- F-21 to F-26: CORS allowlist, docs and debug mode, enumeration and password policy, email change, Docker pinning and non-root user, dependency upgrades.
- F-27 to F-29: frontend race and redirect fixes, schema types, indexes, FKs, migrations, persisted commitments, idempotent plan save.
