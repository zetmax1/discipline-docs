# Release runbook

How to stand up staging on Railway, back up, migrate, deploy, smoke-test and roll back.
The app is three repos — `discipline` (web), `discipline-back` (api), `discipline-py`
(analytics) — each deployed as its own Railway service. Production currently runs the
pre-phase-1 code; the first release carries phases 1–5 at once (branch `fix/phase-5` in all
three repos), including **every migration (00001–00007)**.

Placeholders: `<web>`, `<api>` are the public hostnames of the web and API services;
`$DB_URL` is a Postgres URL for the database being worked on (see §2).

---

## 0. One-time setup

### Release branches
There is no CI. The gate is each repo's check command, run on the exact commit you release:
```bash
cd discipline      && npm ci && npm run check
cd discipline-back && make check
cd discipline-py   && venv/bin/pip install -r requirements-dev.txt && make check
```
All three must pass (lint, types, tests with nothing skipped, vulnerability and secret scans).
Then push `fix/phase-5` in each repo and merge it into `main` (pull request per repo). The
contract test in `discipline-py` reads `../discipline/contracts/`, so run it with `discipline`
checked out at the matching commit.

### Cloudflare Turnstile
Create one widget per environment (Cloudflare dashboard → Turnstile → Add widget), with the
web hostname(s) of that environment. The **site key** goes to the web service
(`VITE_TURNSTILE_SITE_KEY`), the **secret key** to the API (`TURNSTILE_SECRET`).
For local development only, Cloudflare publishes test keys that always pass.

### Secrets
Generate each secret fresh per environment; never reuse production values in staging:
```bash
openssl rand -base64 48   # JWT_SECRET, INTERNAL_JWT_SECRET (different values)
```

---

## 1. Staging on Railway

Create a separate Railway **environment** named `staging` (Project → Environments → New
environment). It must have its own Postgres and Redis, never the production ones.

### Services

| Service | Source repo | Root directory | Build / start | Healthcheck path | Public domain |
|---|---|---|---|---|---|
| `web` | `discipline` | repo root | `npm run build` / `npm start` | — | yes |
| `api` | `discipline-back` | repo root | `Dockerfile` (auto-detected) | `/health` | yes |
| `analytics` | `discipline-py` | repo root | `Procfile` (`uvicorn main:app …`) | `/health` | **no** (private network only) |
| `Postgres` | Railway template | — | — | — | no |
| `Redis` | Railway template | — | — | — | no |

Staging deploys each repo's release branch (`fix/phase-5`, later `main`). Redis holds only
rate-limit and login-throttle windows (TTL ≤ 15 min); it needs no persistence or backups.

### Variables

Names only below; values come from Railway reference variables (`${{Service.VAR}}`) or the
secrets above. Required variables have no defaults: a service refuses to start without them.

**api**

| Variable | Value |
|---|---|
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | `${{Postgres.PGHOST}}`, `${{Postgres.PGPORT}}`, `${{Postgres.PGUSER}}`, `${{Postgres.PGPASSWORD}}`, `${{Postgres.PGDATABASE}}` |
| `DB_SSLMODE` | leave unset (`require`) |
| `JWT_SECRET` | secret, ≥ 32 chars |
| `INTERNAL_JWT_SECRET` | secret, ≥ 32 chars, different from `JWT_SECRET`, **same value as on analytics** |
| `PYTHON_SERVICE_URL` | `http://${{analytics.RAILWAY_PRIVATE_DOMAIN}}:${{analytics.PORT}}` |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` |
| `TURNSTILE_SECRET` | Turnstile secret key of this environment |
| `ALLOWED_ORIGINS` | `https://<web>` (comma-separated, exact origins) |
| `SENTRY_DSN`, `SENTRY_ENVIRONMENT` | optional; `staging` / `production` |
| `ENABLE_IP_DEBUG` | `true` on staging **only while running §1.1**, then delete |
| `TRUSTED_PROXIES` / `TRUSTED_IP_HEADER` | set per §1.1 once confirmed |
| `APP_ENV`, `ENABLE_DOCS` | leave unset |

**analytics**

| Variable | Value |
|---|---|
| `DB_HOST` … `DB_NAME` | same references as the API |
| `INTERNAL_JWT_SECRET` | same value as the API |
| `PORT` | `8082`, set explicitly so the API's `PYTHON_SERVICE_URL` can reference it |
| `SENTRY_DSN`, `SENTRY_ENVIRONMENT` | optional |
| `ENABLE_DOCS` | leave unset |

**web** (Vite reads these at **build** time; redeploy after changing them)

| Variable | Value |
|---|---|
| `VITE_API_URL` | `https://<api>/api` |
| `VITE_TURNSTILE_SITE_KEY` | Turnstile site key of this environment |
| `VITE_SENTRY_DSN`, `VITE_SENTRY_ENVIRONMENT` | optional |

### 1.1 Verify the client-IP header (before trusting any header)

Rate limits and login throttling key on the client IP for anonymous requests. Until this is
confirmed, the API trusts no proxy header and sees Railway's proxy address.

1. On staging set `ENABLE_IP_DEBUG=true` and deploy the API.
2. From two different networks (e.g. Wi-Fi and phone hotspot), run
   `curl -s https://<api>/debug/ip` and note `xForwardedFor`, `xRealIp`, `remoteAddr`, `clientIp`.
3. Also send a forged header and check what survives:
   `curl -s -H 'X-Forwarded-For: 1.2.3.4' -H 'X-Real-IP: 1.2.3.4' https://<api>/debug/ip`
4. The right choice is a header that always holds your real address and that the forged
   request **cannot** change (or a `TRUSTED_PROXIES` range plus `X-Forwarded-For`). No header
   is trusted until this is confirmed.
5. Delete `ENABLE_IP_DEBUG` and redeploy; `/debug/ip` must return 404 again.

### 1.2 Rehearse the migration on staging
Restore a copy of production into the **staging** Postgres (§2), then run §3 and §5 there.
Treat that copy as production data: keep staging access as restricted as production.

---

## 2. Back up

Use the database's public URL (Postgres service → Connect → public network,
`DATABASE_PUBLIC_URL`) with `?sslmode=require` appended. The `pg_dump` major version must be
≥ the server's (`SELECT version();`); a container avoids installing it:

```bash
export DB_URL='postgres://…?sslmode=require'      # never commit or paste it anywhere
STAMP=$(date +%Y%m%d-%H%M)
docker run --rm -e DB_URL -v "$PWD:/backup" postgres:16-alpine \
  sh -c 'pg_dump "$DB_URL" --format=custom --no-owner --no-acl --file /backup/discipline-'"$STAMP"'.dump'
docker run --rm -v "$PWD:/backup" postgres:16-alpine pg_restore --list /backup/discipline-$STAMP.dump | head
```

Keep the file somewhere private and encrypted; it holds users' data and password hashes.
Railway's own volume backups (Postgres service → Backups) are a second layer, not a substitute.

Restore (into an **empty** database, e.g. a fresh Railway Postgres or staging):
```bash
docker run --rm -e DB_URL -v "$PWD:/backup" postgres:16-alpine \
  sh -c 'pg_restore --clean --if-exists --no-owner --no-acl -d "$DB_URL" /backup/discipline-<STAMP>.dump'
```

---

## 3. Migrate

The API never changes the schema and refuses to start until every migration is applied.
Run the migrations from a `discipline-back` checkout of the release commit:

```bash
cd discipline-back
go run ./cmd/migrate -database "$DB_URL" status
go run ./cmd/migrate -database "$DB_URL" up
go run ./cmd/migrate -database "$DB_URL" status     # every migration "applied"
```

What the pending migrations do on production (each runs in a transaction):

| Migration | Effect | If it aborts |
|---|---|---|
| 00001 baseline | No-op on the existing GORM schema | — |
| 00002 typed task columns | `tasks.date` → DATE, times → TIME, composite indexes, user FKs (cascade) | Lists tasks with non-ISO/impossible dates or unparseable times and rows whose user is gone. Nothing changes. Fix or delete those rows, re-run. |
| 00003 user time zone | `users.timezone`, existing users get `Asia/Tashkent` | — |
| 00004 vocabulary per day | **Merges duplicate (user, date, language) words, keeping the oldest** (learned/saved merged). Not reversible. | — |
| 00005 token version | `users.token_version` (all old tokens become invalid: everyone logs in again) | — |
| 00006 task source/plan | `tasks.source`, `tasks.plan_id` | — |
| 00007 vocabulary date | `vocabulary_words.date` → DATE | Lists words whose date is not a real `YYYY-MM-DD`. Nothing changes. Fix or delete, re-run. |

Optional pre-check (read-only) to see problem rows before migrating:
```sql
SELECT id, user_id, date, start_time, end_time FROM tasks
 WHERE date !~ '^\d{4}-\d{2}-\d{2}$' OR start_time !~ '^\d{1,2}:\d{2}$' OR end_time !~ '^\d{1,2}:\d{2}$';
SELECT id, user_id, date FROM vocabulary_words WHERE date !~ '^\d{4}-\d{2}-\d{2}$';
SELECT t.id, t.user_id FROM tasks t LEFT JOIN users u ON u.id = t.user_id WHERE u.id IS NULL;
SELECT v.id, v.user_id FROM vocabulary_words v LEFT JOIN users u ON u.id = v.user_id WHERE v.user_id IS NOT NULL AND u.id IS NULL;
```

---

## 4. Deploy order (first release: phases 1–5)

The old and new code cannot share a database: the old API expects text columns and the old
analytics service trusts `?user_id=`. Do this in a low-traffic window; users are logged out.
If production services auto-deploy from `main`, turn that off (or merge only at the step that
deploys that service) so nothing goes out before the migration.

1. **Staging done:** §1.2 rehearsal and §5 passed on staging with these exact commits, and the
   check command passed in all three repos (§0).
2. **Prepare production variables** (§1 tables) on all three services, including the new
   `REDIS_URL`, `TURNSTILE_SECRET` and Redis service. Rotate `JWT_SECRET` and
   `INTERNAL_JWT_SECRET` (F-02). Don't redeploy yet.
3. **Back up** production (§2). Confirm `pg_restore --list` reads the file.
4. **Migrate** production (§3). From here until step 7, the old API returns errors for task
   and vocabulary requests.
5. **analytics:** deploy `discipline-py` `main`, and remove the service's public domain (F-03).
   Healthcheck `/health` must pass.
6. **api:** deploy `discipline-back` `main`. `/health` must return 200 with `database` and
   `redis` `ok`; Railway keeps the old deployment until it does.
7. **web:** deploy `discipline` `main` (rebuilds with the `VITE_*` values).
8. **Smoke test** (§5). If anything fails and can't be fixed forward in minutes, roll back (§6).
9. Afterwards: delete/rotate the 50 seeded accounts (F-19).

Later releases: check command green on `main` in every repo that changed → migrate (if the
release adds migrations) → analytics → api → web, each waiting for its healthcheck. A contract
change ships in all affected repos in the same release.

---

## 5. Smoke-test checklist

Run against the environment just deployed. Tick every line.

**Platform**
- [ ] `curl -s https://<api>/health` → 200 `{"status":"ok","checks":{"database":"ok","redis":"ok"}}`
- [ ] `curl -s https://<api>/ping` → 200
- [ ] analytics has no public domain; its Railway healthcheck is green
- [ ] `curl -s -o /dev/null -w '%{http_code}' https://<api>/debug/ip` → 404 (unless on §1.1)
- [ ] `curl -s -o /dev/null -w '%{http_code}' https://<api>/swagger/index.html` → 404
- [ ] Responses carry `X-Request-ID`; the same ID appears in the api **and** analytics logs (JSON lines) for one Analytics page load

**Auth**
- [ ] Sign-up shows the Turnstile widget; the button is disabled until it is solved; account is created
- [ ] Sign in works; `GET /api/me` shows the right time zone
- [ ] 3 wrong passwords for one email → the 4th attempt asks for verification
- [ ] Wrong password 4+ times from one browser → the toast says "Try again in N s"; the correct password works after the wait
- [ ] The same account still signs in from another network (no lockout)
- [ ] Log out → the old token gets 401 (`curl -H "Authorization: Bearer <old>" https://<api>/api/me`)

**App**
- [ ] Planner: add a block; an overlapping block → 409 message; mark a block skipped, then add an overlapping block → allowed
- [ ] Dashboard shows today's planned/done and focus score
- [ ] Analytics week/month and focus patterns load (no "Unexpected response")
- [ ] Smart Schedule: generate, save to next week; saving again replaces the plan; a clash with a manual block shows the server's 409 message
- [ ] Vocabulary: today's words load; learned/saved toggles persist
- [ ] Rate limit: 101 quick requests with one token → 429 with `Retry-After`; another user is unaffected

**Observability**
- [ ] If Sentry is configured: an error appears with `request_id` and no body/cookies/Authorization/query string
- [ ] Logs are JSON; no tokens, passwords or query strings in them

---

## 6. Rollback

Decide within the smoke-test window; data written after the backup is lost by a full rollback.

**A. Code only** (no migration in the release, or the schema is fine):
Railway → service → Deployments → the previous deployment → Redeploy. Order: web, api,
analytics (reverse of deploy).

**B. First release (phases 1–5, migrations 00001–00007):**
The old code cannot run on the migrated schema, and `migrate down` cannot undo 00004's merge.
**Do not run `down-to 0`: the baseline's down step drops every table.**
1. Restore the §4 step 3 backup into the database (or into a new Railway Postgres and point
   the services at it) with the restore command in §2.
2. Redeploy the previous (pre-phase-1) deployment of web, api and analytics, and restore the
   old variables (keep the rotated secrets if possible). Revert or hold `main` in each repo so
   a later auto-deploy doesn't bring the new code back.
3. Re-run the parts of §5 that apply to the old version.

**C. Only the phase-5 migration (00007) is the problem:**
`go run ./cmd/migrate -database "$DB_URL" down-to 6` turns `vocabulary_words.date` back into
text; then redeploy an API build from before 00007 (`discipline-back` `fix/phase-4`), which
accepts version 6.

After any rollback, write down what failed before trying again on staging.
