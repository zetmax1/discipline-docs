# Release runbook: phases 1–5

One pass through staging (S1–S12), then production (P1–P12). Production still runs the
pre-phase-1 code; this release ships `fix/phase-5` of all three repos at once, including
**migrations 00001–00007**, and logs every user out.

Every step lists **Do** (the exact command or dashboard action), **OK** (what success looks
like) and **If not** (what to do instead). Never continue past a step that isn't OK.

| Repo | Railway service | Public domain |
|---|---|---|
| `discipline` | `web` | yes |
| `discipline-back` | `api` | yes |
| `discipline-py` | `analytics` | staging: no; production: removed in P11 |

Tools in this folder (`docs/release/`, Python 3 standard library only, never print a secret):
`preflight.py` (variables), `smoke.py` (deployed API), `cleanup.sql` + `check_admin_password.py`
(seeded accounts and admins). Their tests: `python3 -m unittest discover -s docs/release/tests`.

## Conventions

- Run commands from this workspace folder (`discipline_total/`) unless a step says `cd`.
- `<web>`, `<api>` are the public hostnames of the environment you are working on.
- A database URL is the Postgres service's **public** URL (Postgres → Connect → Public network,
  `DATABASE_PUBLIC_URL`) with `?sslmode=require` appended. Read it without echoing, so it
  never lands in shell history or on screen:
  ```bash
  read -rs DB_URL && export DB_URL          # paste, Enter; nothing is shown
  ```
- Deploys use `railway up` from a clean checkout of `fix/phase-5`: it uploads exactly that
  working tree (respecting `.gitignore`), regardless of which branch the service tracks.
  Each repo's `railway.json` sets the start command and healthcheck path (config-as-code
  overrides the dashboard), so Railway only switches traffic once the healthcheck passes.
- `railway variables --service <svc> --environment <env> --kv` prints `KEY=VALUE` lines
  (same as `railway variable list ... --kv`). Only ever pipe it into `preflight.py`.
- Rate limit on `/api/auth/*`: 5 requests a minute per IP. Wait a minute before re-running
  `smoke.py` (each run makes two auth calls on staging, one on production).

### Migrations run from the pre-deploy step (`chore/predeploy-migrate` onwards)

Once `chore/predeploy-migrate` is merged, `discipline-back`'s `railway.json` runs
`["/app/migrate up"]` (one string: Railway's schema allows at most one array item) as the deploy's `preDeployCommand`: Railway runs it in the new image,
once, before that version takes traffic, so the schema is migrated by the same build that will
serve it. A failed pre-deploy step stops the deploy and leaves the old version serving.

- **Back up the database before any destructive migration** (a drop, a type change, a backfill
  that rewrites rows), exactly as in P1, and before the first deploy that carries one. The
  pre-deploy step runs unattended, with nobody watching the output, and `migrate down` cannot
  undo every migration — the dump is the only way back.
- **Check on staging that the pre-deploy step reaches the database over the private network**
  before trusting it in production: the pre-deploy container gets the service's own variables, so
  `DATABASE_URL` (or the `DB_*` variables) must point at `<postgres>.railway.internal` with the
  SSL mode that host accepts, not at a public URL that may not resolve from it. Deploy the api to
  staging, then Deployments → the new deployment → the **pre-deploy** logs: they must show the
  migrations applied (or "no change"), not a connection error, and the deployment must go on to
  pass its healthcheck.
- The manual `go run ./cmd/migrate … up` steps below (S6, P4) stay the rehearsal and the fallback:
  run them when a release needs the schema migrated before the new image exists, and to read
  `status`.

### Dashboard-only settings (not covered by `railway.json`)

Check these once per environment (service → Settings):
- **Source:** repo `discipline` / `discipline-back` / `discipline-py`, root directory = repo
  root, and the **branch** it auto-deploys from (matters in P12).
- **Builder:** `api` uses the Dockerfile (pinned in `railway.json`); `web` and `analytics`
  keep the builder that is configured today.
- **Networking:** public domain on `web` and `api` only; `analytics` reachable on the private
  network (`<service>.railway.internal`).
- **Variables:** per service, as listed in S3.

---

## Staging

### S1. Release commits are green
**Do:** in each repo, on `fix/phase-5`, with a clean working tree:
```bash
cd discipline      && git switch fix/phase-5 && git status --short && npm ci && npm run check; cd ..
cd discipline-back && git switch fix/phase-5 && git status --short && make check; cd ..
cd discipline-py   && git switch fix/phase-5 && git status --short && make check; cd ..
for r in discipline discipline-back discipline-py; do echo "$r $(git -C $r rev-parse --short HEAD)"; done
```
**OK:** no `git status` output, every check ends with `check: all passed` (web: exit 0), and
you note the three commit IDs: staging and production must ship exactly these.
**If not:** stop; fix on `fix/phase-5` (test first) and start again at S1.

### S2. Staging environment exists
**Do:** Railway → Project → Environments → `staging` (or New environment → `staging`). It must
have its **own** `Postgres` and `Redis` services; check the dashboard-only settings above.
`analytics` has no public domain.
**OK:** `staging` lists web, api, analytics, Postgres, Redis; none point at production databases.
**If not:** fix the settings before setting any variable.

### S3. Staging variables
**Do:** on each staging service set the variables below (Variables tab). Generate secrets fresh,
never reuse production values: `openssl rand -base64 48` (one value each for `JWT_SECRET` and
`INTERNAL_JWT_SECRET`). Delete `ANALYTICS_API_KEY` and `JWT_EXPIRY_HOURS` wherever they exist.

| Service | Variables |
|---|---|
| api | `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` = `${{Postgres.PGHOST}}`, `${{Postgres.PGPORT}}`, `${{Postgres.PGUSER}}`, `${{Postgres.PGPASSWORD}}`, `${{Postgres.PGDATABASE}}`; `JWT_SECRET`; `INTERNAL_JWT_SECRET` (same value as analytics); `PYTHON_SERVICE_URL` = `http://${{analytics.RAILWAY_PRIVATE_DOMAIN}}:${{analytics.PORT}}`; `REDIS_URL` = `${{Redis.REDIS_URL}}`; `TURNSTILE_SECRET` = `1x0000000000000000000000000000000AA` (Cloudflare's always-pass **test** secret, needed by `smoke.py`); `ALLOWED_ORIGINS` = `https://<web>`; `ENABLE_IP_DEBUG` = `true` (until S9); optional `SENTRY_DSN`, `SENTRY_ENVIRONMENT=staging`. Leave `DB_SSLMODE`, `APP_ENV`, `ENABLE_DOCS` unset. |
| analytics | the same five `DB_*` references; `INTERNAL_JWT_SECRET` (same as api); `PORT` = `8082`; optional `SENTRY_*`. |
| web | `VITE_API_URL` = `https://<api>/api`; `VITE_TURNSTILE_SITE_KEY` = `1x00000000000000000000AA` (test site key, always passes); optional `VITE_SENTRY_*`. |

**OK:** S4 passes.
**If not:** correct the variables; nothing is deployed yet.

### S4. Preflight staging
**Do:**
```bash
DIG=$(mktemp)
railway variables --service api       --environment staging --kv | python3 docs/release/preflight.py api       --staging --compare "$DIG"
railway variables --service analytics --environment staging --kv | python3 docs/release/preflight.py analytics --staging --compare "$DIG"
railway variables --service web       --environment staging --kv | python3 docs/release/preflight.py web       --staging
rm -f "$DIG"
```
**OK:** every line `PASS` (or `SKIP` on the api run for the two cross-service checks, which the
analytics run then reports as `PASS`); each command exits 0.
**If not:** fix the named variables in Railway and re-run S4. The output names variables only.

### S5. Copy production data into staging (rehearsal data)
**Do:** back up production as in P1 (read-only on production), then restore that dump into the
**staging** Postgres:
```bash
read -rs DB_URL && export DB_URL          # STAGING database URL
docker run --rm -e DB_URL -v "$PWD:/backup" postgres:16-alpine \
  sh -c 'pg_restore --clean --if-exists --no-owner --no-acl -d "$DB_URL" /backup/discipline-<STAMP>.dump'
```
**OK:** exits 0; `psql` on staging shows the production row counts
(`SELECT count(*) FROM users;`). Treat staging as production data from now on.
**If not:** check the URL is staging's and its Postgres is empty; never restore into production.

### S6. Migrate staging
**Do:**
```bash
cd discipline-back
go run ./cmd/migrate -database "$DB_URL" status
go run ./cmd/migrate -database "$DB_URL" up
go run ./cmd/migrate -database "$DB_URL" status     # every migration "applied"
cd ..
```
**OK:** the last `status` shows 00001–00007 applied. See the migration table under P4 for what
each one does.
**If not:** a migration that aborts lists the bad rows and changes nothing. Fix those rows on
staging, note the fix (it must be repeated in production), re-run. Anything else: restore S5
and investigate.

### S7. Deploy staging: analytics, then api, then web
**Do:**
```bash
(cd discipline-py   && railway up --service analytics --environment staging --ci)
(cd discipline-back && railway up --service api       --environment staging --ci)
(cd discipline      && railway up --service web       --environment staging --ci)
curl -s https://<api>/health
```
**OK:** each `railway up` ends with a successful build; each deployment turns "Active" in the
dashboard (healthcheck passed); `/health` prints
`{"checks":{"database":"ok","redis":"ok"},"status":"ok"}`.
**If not:** read the deployment logs (JSON lines). A failed healthcheck leaves the previous
deployment serving. Fix, re-run S1 for that repo, deploy again.

### S8. Smoke test staging
**Do:**
```bash
read -rs STAGING_DB_URL && export STAGING_DB_URL     # staging database URL (deletes the throwaway user)
python3 docs/release/smoke.py https://<api> --staging
```
**OK:** every step `PASS`, an `INFO /debug/ip` line, `delete throwaway user - deleted 1 user(s)`,
`RESULT: PASS`, exit code 0.
**If not:** the failing line says what returned what. The throwaway user is still deleted at
the end; if that step failed, delete it with the email printed at the top:
`DELETE FROM users WHERE email = '<email>';`. Fix and redeploy (S7), then re-run S8.

### S9. Verify the client-IP header, then turn the debug route off
**Do:** from two different networks (e.g. Wi-Fi and phone hotspot):
```bash
curl -s https://<api>/debug/ip
curl -s -H 'X-Forwarded-For: 1.2.3.4' -H 'X-Real-IP: 1.2.3.4' https://<api>/debug/ip
```
Pick a header that always holds your real address and that the forged request **cannot**
change (or a `TRUSTED_PROXIES` range plus `X-Forwarded-For`); set `TRUSTED_IP_HEADER` /
`TRUSTED_PROXIES` on staging api. Then delete `ENABLE_IP_DEBUG` and let the api redeploy.
**OK:** `clientIp` shows your real address from both networks, the forged run does not show
`1.2.3.4` as `clientIp`, and afterwards `curl -s -o /dev/null -w '%{http_code}\n' https://<api>/debug/ip`
prints `404`.
**If not:** leave both variables unset (the API then trusts no header: rate limits key on
Railway's proxy address, safe but coarse) and decide before production.

### S10. Browser check on staging
**Do:** open `https://<web>`: sign up (test widget passes by itself), sign in, add a block,
add an overlapping one, open Dashboard, Analytics (week/month, focus patterns), Smart
Schedule (generate, save next week), Vocabulary; log out.
**OK:** every page loads data; the overlap shows the server's 409 message; no "Unexpected
response"; the same `X-Request-ID` appears in api and analytics logs for one Analytics load.
**If not:** fix, redeploy (S7), repeat S8–S10.

### S11. Rehearse the cleanup on staging
**Do:** with `DB_URL` = staging:
```bash
docker run --rm -i -e DB_URL postgres:16-alpine sh -c 'exec psql "$DB_URL" -X' < docs/release/cleanup.sql
```
**OK:** `seeded_users_found` shows the count (≤ 50, role `user`), `seeded_users_left` 0, then
`ROLLBACK` (dry run: nothing changed), then the list of admins.
For each admin id:
```bash
docker run --rm -e DB_URL postgres:16-alpine sh -c 'exec psql "$DB_URL" -X -At -c "SELECT password FROM users WHERE id = <id>"' \
  | python3 docs/release/check_admin_password.py
```
prints `NO MATCH` (exit 0). `MATCH` (exit 1) means that admin still has the password
`admin123`: note the id; production gets the same fix in P10.
**If not:** a non-`user` role among the seeded accounts or an unexpected admin: stop and
decide per account before production.

### S12. Go / no-go
**OK to continue to production when:** S1–S11 are all OK with the commit IDs from S1, and every
production fix you found (bad rows in S6, admins in S11) is written down.

---

## Production

Low-traffic window. From P3 to P7 the app is down; users are logged out once it is back.

### P1. Back up production
**Do:** before changing anything, save each service's current variables in your password
manager (Variables tab → copy; needed only for a rollback). Then:
```bash
read -rs DB_URL && export DB_URL          # PRODUCTION database URL
STAMP=$(date +%Y%m%d-%H%M)
docker run --rm -e DB_URL -v "$PWD:/backup" postgres:16-alpine \
  sh -c 'pg_dump "$DB_URL" --format=custom --no-owner --no-acl --file /backup/discipline-'"$STAMP"'.dump'
docker run --rm -v "$PWD:/backup" postgres:16-alpine pg_restore --list /backup/discipline-$STAMP.dump | head
```
**OK:** the dump file exists and `pg_restore --list` prints its table of contents. The
`pg_dump` major version must be ≥ the server's (`SELECT version();`). Keep the file private
and encrypted; it holds users' data and password hashes. This folder's `.gitignore` excludes
`*.dump`; move the file somewhere safer once P12 is done.
**If not:** stop. Nothing has changed yet.

### P2. Rotate secrets and set the new variables
**Do:** in production, set the S3 variables with **new** secrets (`openssl rand -base64 48`,
different from staging), the **real** Turnstile keys (Cloudflare dashboard → Turnstile → a
widget for the production web hostname: site key → web `VITE_TURNSTILE_SITE_KEY`, secret →
api `TURNSTILE_SECRET`), `ALLOWED_ORIGINS=https://<web>`, the Redis service and `REDIS_URL`,
and `TRUSTED_IP_HEADER`/`TRUSTED_PROXIES` as decided in S9. No `ENABLE_IP_DEBUG`,
`ENABLE_DOCS`, `APP_ENV`. Delete `ANALYTICS_API_KEY` and `JWT_EXPIRY_HOURS`. Apply the changes.
Railway redeploys the old code with the new values; that is expected (the old API logs
everyone out).
Then:
```bash
DIG=$(mktemp)
railway variables --service api       --environment production --kv | python3 docs/release/preflight.py api       --compare "$DIG"
railway variables --service analytics --environment production --kv | python3 docs/release/preflight.py analytics --compare "$DIG"
railway variables --service web       --environment production --kv | python3 docs/release/preflight.py web
rm -f "$DIG"
```
**OK:** all three runs exit 0 with every line `PASS` (the api run's two `SKIP`s are reported
as `PASS` by the analytics run). This also confirms no Turnstile test key is in production.
**If not:** fix the named variables and re-run. If the old services misbehave with the new
values, that is tolerable for the minutes until P5–P7; if not, restore the saved variables
and stop.

### P3. Stop the API (Gin)
**Do:** `railway down --service api --environment production --yes`
**OK:** the api service has no active deployment;
`curl -s -o /dev/null -w '%{http_code}\n' https://<api>/ping` no longer prints `200`.
**If not:** Railway → api → Deployments → active deployment → ⋮ → Remove.
To abort here: api → Deployments → the removed deployment → Redeploy.

### P4. Migrate production
**Do:**
```bash
cd discipline-back                                 # at fix/phase-5 (S1 commit)
go run ./cmd/migrate -database "$DB_URL" status
go run ./cmd/migrate -database "$DB_URL" up
go run ./cmd/migrate -database "$DB_URL" status     # every migration "applied"
cd ..
```
**OK:** 00001–00007 applied. Each runs in its own transaction:

| Migration | Effect | If it aborts |
|---|---|---|
| 00001 baseline | No-op on the existing GORM schema | — |
| 00002 typed task columns | `tasks.date` → DATE, times → TIME, indexes, user FKs with cascade | Lists the bad task rows; nothing changes. Apply the fix noted in S6, re-run. |
| 00003 user time zone | `users.timezone` (existing users: `Asia/Tashkent`) | — |
| 00004 vocabulary per day | **Merges duplicate (user, date, language) words, keeping the oldest. Not reversible.** | — |
| 00005 token version | `users.token_version` (all old tokens invalid) | — |
| 00006 task source/plan | `tasks.source`, `tasks.plan_id` | — |
| 00007 vocabulary date | `vocabulary_words.date` → DATE | Lists the bad rows; nothing changes. Fix, re-run. |

**If not:** for a listed-rows abort, fix those rows (as rehearsed in S6) and re-run `up`; earlier
migrations stay applied. Anything else: **Rollback B**.

### P5. Deploy analytics
**Do:** `(cd discipline-py && git status --short && git rev-parse --short HEAD && railway up --service analytics --environment production --ci)`
**OK:** clean tree, the S1 commit, build succeeds, deployment Active (healthcheck `/health`
passed: database reachable).
**If not:** read the deployment logs; a failed healthcheck keeps the old deployment. Fix
forward within minutes or **Rollback B**.

### P6. Deploy the API
**Do:** `(cd discipline-back && git status --short && git rev-parse --short HEAD && railway up --service api --environment production --ci)`
then `curl -s https://<api>/health`
**OK:** deployment Active; `/health` prints
`{"checks":{"database":"ok","redis":"ok"},"status":"ok"}`.
**If not:** a startup error names the missing variable (fix it, redeploy); `redis`
`unavailable` → check `REDIS_URL`; else **Rollback B**.

### P7. Deploy the web
**Do:** `(cd discipline && git status --short && git rev-parse --short HEAD && railway up --service web --environment production --ci)`
**OK:** deployment Active; `https://<web>` loads the sign-in page with the Turnstile widget.
**If not:** check the `VITE_*` variables (they are read at build time; redeploy after changing
them); else **Rollback B**.

### P8. Smoke test production (read-only)
**Do:** use an account you own; if none exists, sign up on `https://<web>` (this also checks
the real Turnstile widget). Then:
```bash
export SMOKE_EMAIL='you@example.com'
read -rs SMOKE_PASSWORD && export SMOKE_PASSWORD
python3 docs/release/smoke.py https://<api> --prod
```
**OK:** five `PASS` lines (health, login, dashboard, analytics week, vocabulary), `RESULT: PASS`,
exit 0. Also check in the browser: sign in, planner, dashboard, analytics, smart schedule,
vocabulary; `https://<api>/swagger/index.html` and `https://<api>/debug/ip` return 404.
**If not:** fix forward if it takes minutes; otherwise **Rollback B**.

### P9. Watch the logs for 15 minutes
**Do:** Railway → api and analytics → Logs (and Sentry if configured).
**OK:** JSON lines, no repeated 5xx, no tokens/passwords/query strings in any line.
**If not:** decide fix-forward or **Rollback B** now; later, a rollback loses newer data.

### P10. Remove the seeded accounts; check admins
**Do:** dry run first (`DB_URL` = production):
```bash
docker run --rm -i -e DB_URL postgres:16-alpine sh -c 'exec psql "$DB_URL" -X' < docs/release/cleanup.sql
```
If the counts match S11, edit `docs/release/cleanup.sql`: change the marked `ROLLBACK;` line
to `COMMIT;`, run the same command again, then change it back to `ROLLBACK;`.
Then check each listed admin with `check_admin_password.py` (command in S11).
**OK:** the COMMIT run shows `seeded_users_left` 0 and `COMMIT`; every admin prints `NO MATCH`.
**If not:** unexpected counts or roles: keep `ROLLBACK`, stop and decide per account. An admin
with `MATCH`: sign in as that admin and change the password in the profile (or remove the
admin role: `UPDATE users SET role = 'user' WHERE id = <id>;`), then re-check.

### P11. Remove the analytics public domain
**Do:** Railway → production → analytics → Settings → Networking → Public Networking → delete
the domain (keep private networking).
**OK:** `curl -s -o /dev/null -w '%{http_code}\n' https://<old-analytics-domain>/health` no
longer prints `200`, and `https://<api>/health` still shows `"status":"ok"`, so the API reaches
analytics over the private network. Re-run P8.
**If not:** if `/health` on the api fails, check `PYTHON_SERVICE_URL` uses
`${{analytics.RAILWAY_PRIVATE_DOMAIN}}`; restore the domain only as a last resort.

### P12. Merge `fix/phase-5` into `main` and push
**Do:** first, in each service's Settings → Source, note the **branch** it auto-deploys from.
If it is `main`, pushing `main` triggers a redeploy, which is harmless only if `main` then
equals the commit already running (S1 commit). Then in each repo:
```bash
git switch main && git pull --ff-only
git merge --no-ff fix/phase-5 -m "Merge fix/phase-5: phases 1–5"
git diff --stat fix/phase-5 main          # must print nothing
git push origin main fix/phase-5
git switch fix/phase-5
```
**OK:** `git diff` prints nothing in all three repos; any auto-deploy from `main` goes Active
with the same commit content; `/health` stays `ok`.
**If not:** a merge conflict means `main` has commits that never went through staging: abort
(`git merge --abort`), don't push, and decide before merging. If a service redeploys
something unexpected: Deployments → previous deployment → Redeploy.

---

## Rollback

Decide within the smoke-test window; a full rollback loses data written after P1.

**A. Before P4 (schema untouched):** restore the variables saved in P1, then each service →
Deployments → the previous (pre-release) deployment → Redeploy (the api's removed deployment
too). Re-check the old app in the browser.

**B. After P4 (migrated):** the old code cannot run on the new schema, and `migrate down`
cannot undo 00004. **Never run `down-to 0`: the baseline's down step drops every table.**
1. Stop the api (`railway down --service api --environment production --yes`).
2. Restore the P1 dump into the production database (or into a new Railway Postgres and point
   the services at it):
   ```bash
   docker run --rm -e DB_URL -v "$PWD:/backup" postgres:16-alpine \
     sh -c 'pg_restore --clean --if-exists --no-owner --no-acl -d "$DB_URL" /backup/discipline-<STAMP>.dump'
   ```
3. Restore the variables saved in P1 and redeploy the previous (pre-release) deployment of
   analytics, api and web. Don't push `main` (P12) until the release is retried.
4. Re-check the old app in the browser.

**C. Only migration 00007 is the problem:** `go run ./cmd/migrate -database "$DB_URL" down-to 6`
turns `vocabulary_words.date` back into text; then deploy `discipline-back` at `fix/phase-4`
(`railway up` from that checkout), which accepts schema version 6.

After any rollback, write down what failed and repeat it on staging before trying again.
