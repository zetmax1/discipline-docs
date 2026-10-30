#!/usr/bin/env python3
"""Check one Railway service's variables before a deploy. Prints check names and variable
names only, never a value.

    railway variables --service api --kv       | python3 preflight.py api       --compare /tmp/digests.json
    railway variables --service analytics --kv | python3 preflight.py analytics --compare /tmp/digests.json
    railway variables --service web --kv       | python3 preflight.py web
    (add --staging, and `--environment staging` to the railway command, on staging)

--compare FILE holds only salted SHA-256 digests of the JWT secrets: each run adds its own
service's digests and compares them with the other service's, so the api and analytics runs
can happen in either order. Delete the file afterwards.
Exit code: 0 when nothing failed, 1 otherwise.
"""

import argparse
import hashlib
import hmac
import json
import os
import re
import secrets
import sys

DB = ["DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME"]
REQUIRED = {
    "api": DB + ["JWT_SECRET", "INTERNAL_JWT_SECRET", "PYTHON_SERVICE_URL", "REDIS_URL",
                 "TURNSTILE_SECRET", "ALLOWED_ORIGINS"],
    "analytics": DB + ["INTERNAL_JWT_SECRET", "PORT"],
    "web": ["VITE_API_URL", "VITE_TURNSTILE_SITE_KEY"],
}
REMOVED = ["ANALYTICS_API_KEY", "JWT_EXPIRY_HOURS"]
STAGING_ONLY = ["ENABLE_DOCS", "ENABLE_IP_DEBUG", "APP_ENV"]
SECRETS = {"api": ["JWT_SECRET", "INTERNAL_JWT_SECRET"], "analytics": ["INTERNAL_JWT_SECRET"], "web": []}
MIN_SECRET_LEN = 32

# Cloudflare's documented Turnstile test keys (developers.cloudflare.com/turnstile/troubleshooting/testing/)
TEST_SITE_KEYS = {"1x00000000000000000000AA", "2x00000000000000000000AB", "1x00000000000000000000BB",
                  "2x00000000000000000000BB", "3x00000000000000000000FF"}
TEST_SECRET_PASS = "1x0000000000000000000000000000000AA"
TEST_SECRETS = {TEST_SECRET_PASS, "2x0000000000000000000000000000000AA", "3x0000000000000000000000000000000AA"}

_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


def parse_kv(text: str) -> dict[str, str]:
    """KEY=VALUE lines; a line that doesn't start a new KEY= continues the previous value."""
    out: dict[str, str] = {}
    last = None
    for line in text.splitlines():
        m = _LINE.match(line)
        if m:
            last = m.group(1)
            out[last] = m.group(2)
        elif last is not None:
            out[last] += "\n" + line
    return out


def digest(salt: str, value: str) -> str:
    return hashlib.sha256((salt + "\0" + value).encode()).hexdigest()


class Report:
    def __init__(self) -> None:
        self.failed = False

    def check(self, name: str, ok: bool, names: list[str] | None = None) -> None:
        detail = f" ({', '.join(names)})" if names else ""
        print(f"{'PASS' if ok else 'FAIL'}  {name}{detail if not ok else ''}")
        self.failed |= not ok

    def skip(self, name: str, why: str) -> None:
        print(f"SKIP  {name}: {why}")


def run(service: str, env: dict[str, str], staging: bool, compare: str | None, report: Report) -> None:
    def present(k: str) -> bool:
        return env.get(k, "").strip() != ""

    missing = [k for k in REQUIRED[service] if not present(k)]
    report.check("required variables present", not missing, missing)

    leftover = [k for k in REMOVED if k in env]
    report.check("removed variables absent", not leftover, leftover)

    if staging:
        report.skip("ENABLE_DOCS/ENABLE_IP_DEBUG/APP_ENV unset", "allowed on staging")
    else:
        debug = [k for k in STAGING_ONLY if k in env]
        report.check("ENABLE_DOCS/ENABLE_IP_DEBUG/APP_ENV unset", not debug, debug)

    for k in SECRETS[service]:
        if present(k):
            report.check(f"{k} at least {MIN_SECRET_LEN} characters", len(env[k].strip()) >= MIN_SECRET_LEN, [k])

    if service == "api" and present("JWT_SECRET") and present("INTERNAL_JWT_SECRET"):
        report.check("INTERNAL_JWT_SECRET differs from JWT_SECRET",
                     not hmac.compare_digest(env["JWT_SECRET"].strip(), env["INTERNAL_JWT_SECRET"].strip()),
                     ["INTERNAL_JWT_SECRET", "JWT_SECRET"])

    if service == "api" and present("TURNSTILE_SECRET"):
        secret = env["TURNSTILE_SECRET"].strip()
        if staging:
            report.check("TURNSTILE_SECRET is Cloudflare's always-pass test key (smoke.py --staging needs it)",
                         secret == TEST_SECRET_PASS, ["TURNSTILE_SECRET"])
        else:
            report.check("TURNSTILE_SECRET is not a Cloudflare test key", secret not in TEST_SECRETS,
                         ["TURNSTILE_SECRET"])
    if service == "web" and present("VITE_TURNSTILE_SITE_KEY") and not staging:
        report.check("VITE_TURNSTILE_SITE_KEY is not a Cloudflare test key",
                     env["VITE_TURNSTILE_SITE_KEY"].strip() not in TEST_SITE_KEYS, ["VITE_TURNSTILE_SITE_KEY"])

    if compare and SECRETS[service]:
        cross_check(service, env, compare, report)


def cross_check(service: str, env: dict[str, str], path: str, report: Report) -> None:
    store = {"salt": secrets.token_hex(16), "services": {}}
    if os.path.exists(path):
        with open(path) as f:
            store = json.load(f)
    salt = store["salt"]
    mine = {k: digest(salt, env[k].strip()) for k in SECRETS[service] if env.get(k, "").strip()}
    store["services"][service] = mine
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(store, f, indent=2)

    api, analytics = store["services"].get("api"), store["services"].get("analytics")
    name_same = "INTERNAL_JWT_SECRET identical on api and analytics"
    name_diff = "analytics INTERNAL_JWT_SECRET differs from api JWT_SECRET"
    if not api or not analytics:
        other = "analytics" if service == "api" else "api"
        report.skip(name_same, f"run {other} with the same --compare file")
        report.skip(name_diff, f"run {other} with the same --compare file")
        return
    internal = analytics.get("INTERNAL_JWT_SECRET")
    report.check(name_same, internal is not None and internal == api.get("INTERNAL_JWT_SECRET"),
                 ["INTERNAL_JWT_SECRET"])
    report.check(name_diff, internal is not None and internal != api.get("JWT_SECRET"),
                 ["INTERNAL_JWT_SECRET", "JWT_SECRET"])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("service", choices=sorted(REQUIRED))
    ap.add_argument("--staging", action="store_true", help="allow ENABLE_DOCS/ENABLE_IP_DEBUG/APP_ENV")
    ap.add_argument("--compare", metavar="FILE", help="shared digest file for the api <-> analytics checks")
    args = ap.parse_args(argv)
    if sys.stdin.isatty():
        ap.error("pipe `railway variables --service <name> --kv` into this script")
    env = parse_kv(sys.stdin.read())
    if not env:
        print("FAIL  no KEY=VALUE lines on stdin")
        return 1
    print(f"preflight {args.service} ({'staging' if args.staging else 'production'})")
    report = Report()
    run(args.service, env, args.staging, args.compare, report)
    return 1 if report.failed else 0


if __name__ == "__main__":
    sys.exit(main())
