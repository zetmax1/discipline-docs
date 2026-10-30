# API changes

Contract changes between React ↔ Gin ↔ FastAPI, newest first.

## Phase 5 — public-readiness hardening (branch `fix/phase-5`, monorepo, 2026-10-29)

### Gin → FastAPI (internal)

| | Change |
|---|---|
| `X-Request-ID` | **New header on every proxied call.** Gin sends the request's ID, and FastAPI logs it on every line (`request_id`) and echoes it. FastAPI keeps a well-formed incoming ID (`[A-Za-z0-9._-]{8,128}`) and generates one otherwise. |
| `GET /health` (FastAPI) | Now checks the database (`SELECT 1`): **200** `{status: "ok", checks: {database: "ok"}}` or **503** `{status: "unavailable", checks: {database: "unavailable"}}`. No error details in the body. `Cache-Control: no-store`. |

### React → Gin (public)

| Endpoint | Change |
|---|---|
| `POST /api/tasks`, `POST /api/tasks/bulk`, `PUT /api/tasks/:id`, `PUT /api/tasks/plan` | **Skipped blocks no longer occupy time.** Overlap checks (409) ignore blocks whose `status` is `skipped`, and a skipped block can be moved freely. Changing a block from `skipped` to `pending`/`completed` re-checks its slot and returns **409** if another non-skipped block now overlaps it (the block stays skipped). |
| All rate-limited routes | Limits are **sliding windows kept in Redis**, shared by every API instance and kept across redeploys (they were in-memory token buckets per process). Same limits: 100 requests/min overall, 5/min on `/api/auth/*`, 10/min on `/api/analytics/*`. Every **429** now carries `Retry-After` (seconds). If Redis is unreachable, `/api/auth/*` (including the login failure check) returns **503** `{error}`; other routes go unthrottled and an error is logged. |
| Rate-limit keys | **Authenticated requests are counted per user, not per IP.** The 100/min limit counts per user when the request carries a validly signed, unexpired token (checked before routing, without a DB lookup), and per client IP otherwise (no token, invalid or expired token, CORS preflights, unknown routes). `/api/analytics/*` (10/min) counts per authenticated user. `/api/auth/*` (5/min) still counts per IP. Users behind one NAT no longer share a budget, and a user's budget follows them across IPs. |
| `GET /debug/ip` | **New, off by default.** Only registered when `ENABLE_IP_DEBUG=true`. Returns `{xForwardedFor: [...], xRealIp: [...], remoteAddr, clientIp}`: the raw header values as received (every occurrence), the socket peer, and the IP the limiter uses with the current `TRUSTED_PROXIES`/`TRUSTED_IP_HEADER`. `Cache-Control: no-store`. For checking the platform's proxy behaviour on staging. |
| `POST /api/auth/login` | **The per-email lockout is gone** (anyone could lock out any user). Body accepts optional `turnstileToken` (≤ 2048 chars). Failures are counted in sliding 15-minute windows: **per (email, IP)**, failures 1–3 cost nothing and after failure *n* ≥ 4 the next attempt waits 2^(n−3) s (2, 4, 8 … max 15 min), answered **429** + `Retry-After`; **per IP**, 30 failures (any emails) → **429** + `Retry-After`; **per email**, from 3 failures (any IPs) a Turnstile token is required. Without a valid token the answer is **401** `{error: "Please complete the verification.", captchaRequired: true}` and the password is not checked. Every credential 401 is `{error, captchaRequired}` (true once the next attempt needs a token). A success clears only that (email, IP) delay. Unknown emails behave identically. If Redis or Cloudflare cannot be reached: **503**. |
| `POST /api/auth/register` | **Requires `turnstileToken`.** Missing or rejected → **400** `{error: "Please complete the verification.", captchaRequired: true}`; Cloudflare unreachable → **503**. (`POST /api/admin/register` is unchanged: no captcha.) |
| All responses | **New `X-Request-ID` header.** A well-formed incoming `X-Request-ID` (`[A-Za-z0-9._-]{8,128}`) is kept, anything else is replaced by 32 hex characters. The same ID is in the API's and the analytics service's JSON logs. Panics now return **500** `{error: "Internal server error"}` (JSON). |
| `GET /health` | **New.** Checks Postgres and Redis (2 s timeout each, run in parallel): **200** `{status: "ok", checks: {database, redis}}` or **503** `{status: "unavailable", checks: {...: "unavailable"}}` with no error details. `Cache-Control: no-store`. `/ping` stays as a liveness check that touches nothing. |

Frontend updates shipped in the same phase:
- Sign-up always shows the Cloudflare Turnstile widget (`VITE_TURNSTILE_SITE_KEY`); the button is disabled until it is solved.
- Sign-in shows the widget once the server answers `captchaRequired`, and sends a fresh token with each attempt.
- A 429 toast says how many seconds to wait (`Retry-After`).
- API errors are `ApiError` (same message as before, plus `status`, body and `retryAfter`).

### Database

| | Change |
|---|---|
| `vocabulary_words.date` | Migration `00007` changes it from `text` to `DATE`. It aborts without changes and lists the rows if any date is not a real `YYYY-MM-DD`. JSON is unchanged (`"YYYY-MM-DD"`). The API refuses to start until migrations are at the latest version. |

## Phase 4 — schedule/vocabulary fixes, dependencies (branch `fix/phase-4`, 2026-10-29)

### Gin → FastAPI (internal)

| Endpoint | Change |
|---|---|
| `POST /analytics/smart-schedule` request | **Validated:** `startTime`/`endTime` `HH:MM` 00:00–24:00, `endTime` ≠ `startTime` (earlier = overnight), `days` 1–7 unique names `Monday`…`Sunday`, goals 0–80 h in 0.5 steps (finite), ≤ 50 commitments. Bad input returns **422** `{error: "commitments[0].startTime: must be HH:MM between 00:00 and 24:00; …", details: [{field, message}]}`; it no longer returns 500. |
| `POST /analytics/smart-schedule` response | **New fields:** `placed_minutes` and `shortfall_minutes`, per category (`deep-work`, `study`, `rest`). Blocks are on 30-minute boundaries, never start before 06:00, never cross midnight, and total exactly the requested goal hours unless reported as shortfall. `reasoning` says "learned from your history" only with ≥ 10 completed blocks of that category in 30 days; otherwise "Default placement — not enough history yet". |
| All FastAPI validation errors | 422 body is `{error, details}` instead of FastAPI's default `{detail: [...]}`. |

### React → Gin (public)

| Endpoint | Change |
|---|---|
| `POST /api/analytics/smart-schedule` | Gin rejects only malformed bodies itself (bad JSON, unknown fields, wrong types, trailing data, size caps: **400**). Value errors come from the analytics service as **422** `{error, details}`, relayed unchanged. The response includes `placed_minutes`/`shortfall_minutes`, and the frontend contract (`smart_schedule`) covers it. |
| `PUT /api/tasks/plan` | **New.** Body `{weekStart: "YYYY-MM-DD" (a Monday), tasks: [CreateTask…] (0–200)}`. In one transaction it deletes the blocks previously saved by a plan for that Monday–Sunday week and inserts these with a new `plan_id`; manual blocks are never touched. Returns `{planId, count, replaced}`. Invalid input → **400**; overlap with a manual block or within the plan → **409**, leaving the old plan in place. |
| Task JSON | **New fields:** `source` (`"manual"` / `"smart-schedule"`) and `planId` (only on generated blocks). |
| `GET /api/vocabulary/*` | English words use the dictionary meaning matching the word's intended part of speech (first meaning otherwise), with `definition` ≤ 300 characters. Russian words now carry `partOfSpeech: "noun"`. |

Frontend updates shipped in the same phase:
- Smart Schedule shows the 422 message and any shortfall, has a day picker per commitment (default Mon–Fri), and shows each commitment's days.
- "Save Weekly Plan" asks for the target week (default next Mon–Sun) and uses `PUT /api/tasks/plan`.
- Commitments and goals persist in localStorage.
- The CEFR badge is removed.

## Phase 3 — analytics correctness (branch `fix/phase-3`, 2026-10-29)

**Contract file.** The frontend now owns the contract.
- `discipline/src/contracts/analytics.ts` holds zod schemas, and the UI parses responses with them; a mismatch shows "Unexpected response …" instead of rendering empty data.
- `discipline/contracts/analytics.schema.json` is the exported JSON Schema; run `npm run contract:update` after changing a schema.
- `discipline-py/tests/test_contract.py` validates the real responses against that file.
- Objects are open: the server may add fields, but must not drop, rename or retype any listed field.

### Metric definitions (one module: `discipline-py/app/metrics.py`)

For day D in the user's zone, a block is **due** once its end time has passed.

| Field | Definition |
|---|---|
| `planned_minutes` / `completed_minutes` ("Planned" / "Done") | All of D's blocks / D's completed blocks, including blocks finished early. |
| `completion` | Completed minutes of due blocks ÷ planned minutes of due blocks. `null` when nothing is due. |
| `deep` | min(1, completed deep-work minutes ÷ 180). |
| `distraction` | max(0, 1 − distractions per completed deep-work hour ÷ 4); 0 when no deep work was completed. |
| `focus_score` | Round half up of 100 × (0.5·completion + 0.3·deep + 0.2·distraction). `null` when nothing is due; the UI shows "—", never 0. |
| Week/month `focus_score` | Mean of the daily scores that exist (one decimal). |
| `streak` | Counting back from yesterday: days with nothing due are skipped, a day at ≥ 70% completion counts, the first day below 70% ends it. |

### Gin → FastAPI (internal)

| Endpoint | Change |
|---|---|
| `GET /analytics/today` | **New.** `DayMetrics` fields plus `daily_deep_work_target_minutes`. |
| `GET /analytics/weekly`, `/analytics/monthly` | **New shape** (`PeriodReport`): `range`, `start_date`, `end_date` (clamped to today), `period_end_date`, `focus_score`, `planned_minutes`, `completed_minutes`, `deep_work_minutes`, `days[]`, `category_minutes[]`, `streak`, `comparison {previous_focus_score, change}`, `patterns`, `charts {focus_gauge, category_distribution}`. Replaces `report`/`analysis`/`daily_breakdown`/`weekly_breakdown`/`metrics`. |
| `patterns` (inside the report) | Covers the trailing 30 days up to today. If fewer than 7 days had due blocks: `{insufficient_data: true, days_needed, days_with_data, window_days}`. Otherwise: `{insufficient_data: false, days_with_data, window_days, best_weekday, peak_hour, trend, consistency_score, insights[]}`. |
| `GET /analytics/focus-patterns?days=` | **New shape:** `start_date`, `end_date`, `days`, `heatmap {weekdays, hours 0–23, values 7×24}` (completed deep-work hours by minute overlap), `productivity_by_weekday[] {day, focus_score}`, `deep_work_by_slot[] {label, minutes}`, `distraction_trend[] {date, distractions_per_hour}`, `charts {focus_heatmap, distraction_trend}`. The old `data.*` wrapper is gone. |
| Charts | Each chart is `{image: base64 PNG, data: <plotted series/matrix>}` instead of a bare string. A chart with nothing to draw gets a "No data yet" placeholder image. Images are cached for 5 min. |
| `GET /analytics/productivity-trend` | **Removed** (unused by Gin; its patterns now live in the report). |
| All routes | Declare Pydantic `response_model`s (`app/schemas.py`). |

### React → Gin (public)

| Endpoint | Change |
|---|---|
| `GET /api/dashboard/stats` | **Removed**, along with its Go-side formula. |
| `GET /api/dashboard/today` | **New.** Authenticated; proxies `/analytics/today` (same body). |
| `GET /api/analytics?range=`, `/api/analytics/focus-patterns` | The body is the new Python shape above, passed through unchanged. |

Frontend updates shipped in the same phase:
- The Dashboard reads `/api/dashboard/today` and shows Planned/Done, deep work against the target, and the score with its breakdown.
- The Analytics page reads the new report and shows "Log N more days to see patterns." when there isn't enough data.
- Login toasts show the actual error.
- Demo mode shows "Not available in demo mode" on Analytics and Smart Schedule, and no longer loops on 401.

## Phase 2 — data foundation (branch `fix/phase-2`, 2026-10-29)

### Gin → FastAPI (internal)

| | Change |
|---|---|
| Internal JWT | New required claim `tz` holds the user's IANA zone, e.g. `Asia/Tashkent`. If it's missing, empty or unknown, FastAPI returns **401**. All today/week/month and trailing-N-day boundaries use this zone. |
| DB types read by Python | `tasks.date` is now `DATE` and `start_time`/`end_time` are `TIME`. Python still gets `"YYYY-MM-DD"`/`"HH:MM"` strings (per-connection psycopg2 casters), and `"24:00"` survives. |

### React → Gin (public)

| Endpoint | Change |
|---|---|
| All authenticated endpoints | Tokens must carry `tv` (the user's token version). Tokens issued before this phase, or before the user's last logout or password change, get **401**. After deploy, every user logs in again. Access tokens now last **24h** (was 72h by default). |
| `POST /api/auth/logout` | **New.** Authenticated; returns **204**. Revokes every token of the user (all devices). |
| `GET /api/me`, login/register responses | `user.timezone` (IANA name) added. |
| `PUT /api/me` | Accepts `timezone`; it must load with Go's `time.LoadLocation`, and `"Local"` is rejected (**400**). After a password change, the response includes `token`, a replacement for the now-revoked current token. |
| `GET /api/tasks`, `/api/dashboard/stats`, `/api/vocabulary/today` (no `date`) | The default date is "today" in the user's time zone, not the server's. |
| `POST /api/tasks`, `POST /api/tasks/bulk`, `PUT /api/tasks/:id` | Validated server-side: real `YYYY-MM-DD` date; zero-padded `HH:MM` times; `endTime` after `startTime` and at most `24:00` (no midnight crossing); `category` ∈ deep-work/study/admin/gym/rest; `status` ∈ pending/completed/skipped; `energy` 1–5; `distractions` 0–100; `name` 1–120 chars (trimmed). Violations return **400**. A block overlapping another of the user's blocks on the same date returns **409**; touching blocks are allowed. On update, time order and overlap are only checked when `date`/`startTime`/`endTime` change. Bulk is all-or-nothing. |
| `PUT /api/tasks/:id`, `DELETE /api/tasks/:id`, `PUT /api/vocabulary/:id/*` | A missing row is 404; a database failure is now **500** (it used to be 404). Updates write only the fields sent. |
| `POST /api/tasks/:id/distractions` | **New.** Body `{"delta": 1}` or `{"delta": -1}` is an atomic increment, clamped to 0–100, and returns `{"task": …}`. Any other delta is **400**; another user's or a missing task is **404**. |
| `GET /api/vocabulary/today?date=` | `date` must be a real `YYYY-MM-DD` and at most one day after today in the user's zone, otherwise **400**. If the dictionary lookup fails, the English word comes back with **`id: 0`**. It is not stored, and the next request retries. |
| Task JSON | Unchanged: `date` is `"YYYY-MM-DD"`, `startTime`/`endTime` are `"HH:MM"` (`"24:00"` allowed as an end time). |

Frontend updates shipped in the same phase:
- `localDateString()` replaces UTC date slicing everywhere, and a weekly plan saves local dates.
- The profile modal can edit the time zone and stores the replacement token.
- Logout calls `/api/auth/logout`.
- The Planner uses the distractions endpoint.
- Unsaved (`id: 0`) words have no learned/saved buttons.
- The Planner shows the server's 400/409 message when adding a block fails. Failed updates and deletes show an error toast.

## Phase 1 — security (branch `fix/phase-1`, 2026-10-29)

### Gin → FastAPI (internal)

| | Before | After |
|---|---|---|
| Caller identity | `?user_id=<id>` query param on every call | `Authorization: Bearer <JWT>`; HS256 with `INTERNAL_JWT_SECRET`, claims `sub` = user id (string), `aud` = `discipline-py`, `iat`, `exp` = now + 60s |
| Service auth | `X-API-Key: <ANALYTICS_API_KEY>` | Removed. The JWT above is the only credential. |
| `user_id` param | Required on all `/analytics/*` routes | Removed. Any `user_id` sent is ignored. |
| Missing or invalid token | 403 `Invalid API Key` | 401 `Invalid or missing internal token`, `WWW-Authenticate: Bearer` |
| `POST /analytics/smart-schedule` body | Client body streamed through unchanged | Gin decodes and validates it, then re-encodes. Python receives only `commitments` and `goals`. |
| `/docs`, `/redoc`, `/openapi.json` | Always public | Only served when `ENABLE_DOCS=true` |
| CORS | `*` with credentials | No CORS headers at all (not browser-facing) |
| Base URL | Default `https://discipline-py.up.railway.app` | No default; `PYTHON_SERVICE_URL` is required (Railway private network) |

### React → Gin (public)

| Endpoint | Change |
|---|---|
| `GET /api/analytics?range=` | `range` must be `week` or `month` (empty defaults to `week`). Anything else returns **400** (it used to fall back to weekly silently). |
| `GET /api/analytics/focus-patterns?days=` | `days` must be an integer from 7 to 365 (empty defaults to 30). Anything else returns **400**. |
| `POST /api/analytics/smart-schedule` | Strict body, unknown fields rejected with **400**: `commitments` ≤ 50 items; each needs `id` (≤ 64 chars), `name` (1–100), `startTime`/`endTime` as `HH:MM` 00:00–23:59, and `days` (1–7 values from `Monday`…`Sunday`). `goals` is required; `deepWorkHours`/`studyHours`/`restHours` are optional numbers 0–168. |
| `GET/POST /api/analytics*` errors | Upstream connection failures, timeouts (10s) and responses over 10 MB return **502** (was 500). |
| `POST /api/auth/register`, `POST /api/admin/register` | The password must be at least 10 characters and at most 72 bytes. Violations return **400** (they used to get 409 or a 6-char minimum). A duplicate email still returns **409**. |
| `POST /api/auth/login` | After 5 failed attempts within 15 min for one email (existing or not), returns **429** with a `Retry-After` header for 15 min. Non-credential failures return 500 instead of 401. |
| `PUT /api/me` | Changing `email` now requires `oldPassword` (400 without it or if it's wrong). `email` must be a valid address; `name` ≤ 100 chars; `newPassword` follows the register policy. |
| `POST /api/tasks/bulk` | `tasks` must have 1–200 items (400 otherwise). Inserts are all-or-nothing. |
| All endpoints | Request bodies over 1 MB return **413**. |
| CORS | Only exact `ALLOWED_ORIGINS` matches get `Access-Control-Allow-Origin` (plus `Vary: Origin`). Preflights from other origins get **403**. |
| `/swagger/*` | Only served when `ENABLE_DOCS=true`. |

Frontend updates shipped in the same phase:
- Register form checks the password policy and shows the hint.
- The profile modal sends `oldPassword` with an email change and checks the policy for a new password.
