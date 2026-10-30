#!/usr/bin/env python3
"""Smoke-test a deployed API. One line per step: status, latency, step. Exit 1 on any failure.

    STAGING_DB_URL='postgres://...?sslmode=require' python3 smoke.py https://<api-staging> --staging
    SMOKE_EMAIL=... SMOKE_PASSWORD=... python3 smoke.py https://<api> --prod

--staging (writes): health, register a throwaway user (Turnstile dummy token: the staging API
  must use Cloudflare's always-pass test secret), login, create a block, list today, dashboard,
  analytics week/month, focus patterns, generate + save next week's smart schedule, vocabulary,
  logout and check the old token is rejected, /debug/ip if enabled. Finally deletes the
  throwaway user (cascades to its blocks and words) with psql in a postgres:16-alpine container
  (needs Docker); the URL comes from the variable named by --db-url-env, never from argv.
--prod (no writes of its own): health, login as SMOKE_EMAIL/SMOKE_PASSWORD, dashboard,
  analytics week, vocabulary today. Note: the first vocabulary call of a day stores that day's
  words for the account, as opening the page does.

Never prints passwords, tokens or the database URL. Python 3 standard library only.
"""

import argparse
import datetime as dt
import json
import os
import secrets
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from zoneinfo import ZoneInfo

TURNSTILE_DUMMY_TOKEN = "XXXX.DUMMY.TOKEN.XXXX"  # accepted only by Cloudflare's test secret keys
TIMEOUT = 30
MAX_BODY = 1 << 20
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
TODAY_KEYS = {"date", "planned_minutes", "completed_minutes", "focus_score"}


class StepFailed(Exception):
    pass


class Smoke:
    def __init__(self, base: str) -> None:
        base = base.rstrip("/")
        self.base = base[:-4] if base.endswith("/api") else base
        self.failed = False

    def call(self, method: str, path: str, token: str | None = None, body: object = None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method)
        req.add_header("Accept", "application/json")
        req.add_header("User-Agent", "discipline-smoke/1")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        if token:
            req.add_header("Authorization", "Bearer " + token)
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                status, raw = resp.status, resp.read(MAX_BODY)
        except urllib.error.HTTPError as e:
            status, raw = e.code, e.read(MAX_BODY)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise StepFailed(f"no response: {getattr(e, 'reason', e)}") from None
        try:
            return status, json.loads(raw)
        except ValueError:
            return status, raw.decode(errors="replace")

    def expect(self, method: str, path: str, want: int, token: str | None = None, body: object = None):
        status, payload = self.call(method, path, token, body)
        if status != want:
            err = payload.get("error") if isinstance(payload, dict) else str(payload)
            raise StepFailed(f"HTTP {status}, want {want}: {str(err)[:200]}")
        return payload

    def step(self, name: str, fn):
        """Run one step and print its line; re-raises so the run stops at the first failure."""
        start = time.monotonic()
        try:
            detail = fn()
        except StepFailed as e:
            self.line("FAIL", name, start, str(e))
            self.failed = True
            raise
        self.line("PASS", name, start, str(detail) if detail else "")
        return detail

    @staticmethod
    def line(status: str, name: str, start: float, detail: str = "") -> None:
        ms = (time.monotonic() - start) * 1000
        print(f"{status:<4}  {ms:7.0f} ms  {name}{'  - ' + detail if detail else ''}", flush=True)


def need(cond: bool, why: str) -> None:
    if not cond:
        raise StepFailed(why)


def check_health(s: Smoke) -> str:
    body = s.expect("GET", "/health", 200)
    need(isinstance(body, dict) and body.get("status") == "ok", f"unexpected body {body}")
    return ", ".join(f"{k} {v}" for k, v in body.get("checks", {}).items())


def login(s: Smoke, email: str, password: str) -> str:
    body = s.expect("POST", "/api/auth/login", 200, body={"email": email, "password": password})
    need(isinstance(body, dict) and bool(body.get("token")), "no token in the response")
    return body["token"]


def today_in_user_zone(s: Smoke, token: str) -> dt.date:
    me = s.expect("GET", "/api/me", 200, token)
    tz = (me.get("user") or me).get("timezone") if isinstance(me, dict) else None
    need(bool(tz), "no timezone in /api/me")
    return dt.datetime.now(ZoneInfo(tz)).date()


def run_prod(s: Smoke) -> None:
    email, password = os.environ.get("SMOKE_EMAIL", ""), os.environ.get("SMOKE_PASSWORD", "")
    if not email or not password:
        sys.exit("set SMOKE_EMAIL and SMOKE_PASSWORD (an existing account) for --prod")
    s.step("api health", lambda: check_health(s))
    state: dict = {}
    s.step("login (SMOKE_EMAIL)", lambda: state.update(token=login(s, email, password)))
    token = state["token"]
    s.step("dashboard today", lambda: dashboard(s, token, None))
    s.step("analytics week", lambda: report(s, token, "week"))
    s.step("vocabulary today", lambda: vocabulary(s, token))


def dashboard(s: Smoke, token: str, today: dt.date | None) -> str:
    body = s.expect("GET", "/api/dashboard/today", 200, token)
    need(isinstance(body, dict) and TODAY_KEYS <= body.keys(), "missing keys in the response")
    if today is not None:
        need(body["date"] == today.isoformat(), f"date {body['date']}, want {today}")
    return f"planned {body['planned_minutes']} min"


def report(s: Smoke, token: str, kind: str) -> str:
    body = s.expect("GET", f"/api/analytics?range={kind}", 200, token)
    need(isinstance(body, dict) and body.get("range") == kind, f"range {body.get('range')!r}")
    return f"{body['start_date']}..{body['end_date']}"


def vocabulary(s: Smoke, token: str) -> str:
    body = s.expect("GET", "/api/vocabulary/today", 200, token)
    need(isinstance(body, dict) and "words" in body, "no words in the response")
    return f"{body.get('count')} word(s)"


def run_staging(s: Smoke, db_url_env: str) -> None:
    if not os.environ.get(db_url_env):
        sys.exit(f"set {db_url_env} to the staging database URL (needed to delete the throwaway user)")
    if not shutil.which("docker"):
        sys.exit("docker is required to delete the throwaway user")
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%d%H%M%S")
    email = f"smoke-{stamp}-{secrets.token_hex(3)}@example.com"
    password = secrets.token_urlsafe(24)
    print(f"throwaway user: {email}")
    registered = False
    try:
        s.step("api health", lambda: check_health(s))

        def register():
            nonlocal registered
            body = s.expect("POST", "/api/auth/register", 201, body={
                "name": "Smoke Test", "email": email, "password": password,
                "turnstileToken": TURNSTILE_DUMMY_TOKEN})
            registered = True
            need(isinstance(body, dict) and bool(body.get("token")), "no token in the response")
        s.step("register throwaway user", register)

        state: dict = {}
        s.step("login", lambda: state.update(token=login(s, email, password)))
        token = state["token"]
        today = s.step("today in the user's time zone", lambda: today_in_user_zone(s, token))

        def create_block():
            body = s.expect("POST", "/api/tasks", 201, token, {
                "name": "Smoke test block", "category": "deep-work", "startTime": "09:00",
                "endTime": "10:00", "energy": 3, "date": today.isoformat()})
            task = body.get("task", body) if isinstance(body, dict) else {}
            need(bool(task.get("id")), "no task id in the response")
            state["task_id"] = task["id"]
            return f"id {task['id']} on {today}"
        s.step("create block", create_block)

        def list_today():
            body = s.expect("GET", f"/api/tasks?date={today.isoformat()}", 200, token)
            ids = [t.get("id") for t in body.get("tasks", [])]
            need(state["task_id"] in ids, "the new block is not listed")
            return f"{len(ids)} block(s)"
        s.step("list today", list_today)
        s.step("dashboard today", lambda: dashboard(s, token, today))
        s.step("analytics week", lambda: report(s, token, "week"))
        s.step("analytics month", lambda: report(s, token, "month"))

        def focus_patterns():
            body = s.expect("GET", "/api/analytics/focus-patterns", 200, token)
            need(isinstance(body, dict) and "heatmap" in body, "no heatmap in the response")
            return f"{body.get('days')} days"
        s.step("focus patterns", focus_patterns)

        def generate():
            body = s.expect("POST", "/api/analytics/smart-schedule", 200, token, {
                "commitments": [{"id": "work", "name": "Work", "startTime": "09:00", "endTime": "17:00",
                                 "days": DAYS[:5]}],
                "goals": {"deepWorkHours": 5, "studyHours": 3, "restHours": 2}})
            blocks = [b for b in body.get("blocks", []) if b.get("category") != "fixed"]
            need(bool(blocks), "no blocks generated")
            state["blocks"] = blocks
            return f"{len(blocks)} block(s)"
        s.step("generate smart schedule", generate)

        def save_week():
            week_start = today + dt.timedelta(days=7 - today.weekday())  # next Monday
            tasks = [{"name": b["name"], "category": b["category"], "startTime": b["startTime"],
                      "endTime": b["endTime"], "energy": 5 if b["category"] in ("deep-work", "study") else 3,
                      "date": (week_start + dt.timedelta(days=DAYS.index(b["day"]))).isoformat()}
                     for b in state["blocks"]]
            body = s.expect("PUT", "/api/tasks/plan", 200, token, {"weekStart": week_start.isoformat(), "tasks": tasks})
            need(body.get("count") == len(tasks), f"saved {body.get('count')} of {len(tasks)}")
            return f"{len(tasks)} block(s) for the week of {week_start}"
        s.step("save smart schedule week", save_week)
        s.step("vocabulary today", lambda: vocabulary(s, token))
        s.step("logout", lambda: s.expect("POST", "/api/auth/logout", 204, token) and None)
        s.step("old token rejected", lambda: s.expect("GET", "/api/me", 401, token) and None)

        start = time.monotonic()
        status, body = s.call("GET", "/debug/ip")
        if status == 200:
            s.line("INFO", "/debug/ip", start, json.dumps(body, separators=(",", ":")))
        else:
            s.line("INFO", "/debug/ip", start, f"not enabled (HTTP {status})")
    except StepFailed:
        pass
    finally:
        try:
            s.step("delete throwaway user", lambda: delete_user(email, db_url_env, registered))
        except StepFailed:
            pass


def delete_user(email: str, db_url_env: str, registered: bool) -> str:
    """DELETE the throwaway user by its generated email; tasks and words cascade."""
    need(email.startswith("smoke-") and email.endswith("@example.com"), "refusing to delete a non-smoke email")
    env = dict(os.environ, DB_URL=os.environ[db_url_env], SMOKE_EMAIL=email)
    script = 'exec psql "$DB_URL" -X -q -At -v ON_ERROR_STOP=1 -v email="$SMOKE_EMAIL"'
    sql = "DELETE FROM users WHERE email = :'email' RETURNING id;\n"
    try:
        out = subprocess.run(
            ["docker", "run", "--rm", "-i", "-e", "DB_URL", "-e", "SMOKE_EMAIL", "postgres:16-alpine", "sh", "-c", script],
            input=sql, capture_output=True, text=True, env=env, timeout=180)
    except subprocess.TimeoutExpired:
        raise StepFailed("psql timed out") from None
    if out.returncode != 0:
        raise StepFailed(f"psql exit {out.returncode}: {out.stderr.strip()[-200:]}")
    rows = [line for line in out.stdout.splitlines() if line.strip()]
    # After a successful registration exactly one row must go; otherwise at most one may exist.
    need(len(rows) == 1 if registered else len(rows) <= 1, f"deleted {len(rows)} row(s)")
    return f"deleted {len(rows)} user(s)"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("base_url", help="the API's public origin, e.g. https://<api>")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--staging", action="store_true", help="full run with a throwaway user (writes)")
    mode.add_argument("--prod", action="store_true", help="read-only run as SMOKE_EMAIL")
    ap.add_argument("--db-url-env", default="STAGING_DB_URL",
                    help="name of the variable holding the staging DB URL (default STAGING_DB_URL)")
    args = ap.parse_args()
    s = Smoke(args.base_url)
    print(f"smoke {'staging' if args.staging else 'production'}: {s.base}")
    try:
        run_staging(s, args.db_url_env) if args.staging else run_prod(s)
    except StepFailed:
        pass
    print("RESULT: " + ("FAIL" if s.failed else "PASS"))
    return 1 if s.failed else 0


if __name__ == "__main__":
    sys.exit(main())
