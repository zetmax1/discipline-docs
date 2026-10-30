"""python3 -m unittest discover -s docs/release/tests"""

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import preflight  # noqa: E402

JWT = "j" * 40
INTERNAL = "i" * 40
DB = "DB_HOST=h\nDB_PORT=5432\nDB_USER=u\nDB_PASSWORD=dbpass-value\nDB_NAME=n\n"
API = (DB + f"JWT_SECRET={JWT}\nINTERNAL_JWT_SECRET={INTERNAL}\nPYTHON_SERVICE_URL=http://a:1\n"
       "REDIS_URL=redis://r:6379\nTURNSTILE_SECRET=0x4AAAAAAAreal-secret\nALLOWED_ORIGINS=https://w\n")
ANALYTICS = DB + f"INTERNAL_JWT_SECRET={INTERNAL}\nPORT=8082\n"
WEB = "VITE_API_URL=https://a/api\nVITE_TURNSTILE_SITE_KEY=0x4AAAAAAAreal-site-key\n"


def run(service, stdin, *args):
    out = io.StringIO()
    sys_stdin = sys.stdin
    sys.stdin = io.StringIO(stdin)
    try:
        with contextlib.redirect_stdout(out):
            code = preflight.main([service, *args])
    finally:
        sys.stdin = sys_stdin
    return code, out.getvalue()


class PreflightTest(unittest.TestCase):
    def assertNoValues(self, output, *values):
        for v in values:
            self.assertNotIn(v, output)

    def test_clean_services_pass(self):
        for service, env in (("api", API), ("analytics", ANALYTICS), ("web", WEB)):
            code, out = run(service, env)
            self.assertEqual(code, 0, out)
            self.assertNotIn("FAIL", out)
            self.assertNoValues(out, JWT, INTERNAL, "dbpass-value", "real-secret")

    def test_missing_and_removed_variables_fail_by_name(self):
        env = API.replace("REDIS_URL=redis://r:6379\n", "") + "ANALYTICS_API_KEY=old-key-value\nJWT_EXPIRY_HOURS=720\n"
        code, out = run("api", env)
        self.assertEqual(code, 1)
        self.assertIn("FAIL  required variables present (REDIS_URL)", out)
        self.assertIn("FAIL  removed variables absent (ANALYTICS_API_KEY, JWT_EXPIRY_HOURS)", out)
        self.assertNoValues(out, "old-key-value")

    def test_short_or_shared_secrets_fail(self):
        code, out = run("api", API.replace(JWT, "short").replace(INTERNAL, "short"))
        self.assertEqual(code, 1)
        self.assertIn("FAIL  JWT_SECRET at least 32 characters", out)
        self.assertIn("FAIL  INTERNAL_JWT_SECRET differs from JWT_SECRET", out)
        self.assertNoValues(out, "short (")

    def test_debug_flags_only_on_staging(self):
        env = API + "ENABLE_DOCS=true\nAPP_ENV=development\n"
        code, out = run("api", env)
        self.assertEqual(code, 1)
        self.assertIn("(ENABLE_DOCS, APP_ENV)", out)
        staging = env.replace("0x4AAAAAAAreal-secret", preflight.TEST_SECRET_PASS)
        code, out = run("api", staging, "--staging")
        self.assertEqual(code, 0, out)

    def test_turnstile_test_keys_rejected_in_production_required_on_staging(self):
        code, out = run("api", API.replace("0x4AAAAAAAreal-secret", preflight.TEST_SECRET_PASS))
        self.assertIn("FAIL  TURNSTILE_SECRET is not a Cloudflare test key", out)
        code, out = run("api", API, "--staging")
        self.assertIn("FAIL  TURNSTILE_SECRET is Cloudflare's always-pass test key", out)
        code, out = run("web", WEB.replace("0x4AAAAAAAreal-site-key", "1x00000000000000000000AA"))
        self.assertEqual(code, 1)

    def test_compare_file_checks_across_runs_in_either_order(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "digests.json")
            code, out = run("analytics", ANALYTICS, "--compare", path)
            self.assertEqual(code, 0, out)
            self.assertIn("SKIP  INTERNAL_JWT_SECRET identical", out)
            code, out = run("api", API, "--compare", path)
            self.assertEqual(code, 0, out)
            self.assertIn("PASS  INTERNAL_JWT_SECRET identical on api and analytics", out)
            self.assertIn("PASS  analytics INTERNAL_JWT_SECRET differs from api JWT_SECRET", out)
            stored = Path(path).read_text()
            self.assertNoValues(stored, JWT, INTERNAL)
            self.assertEqual(os.stat(path).st_mode & 0o777, 0o600)
            self.assertEqual(set(json.loads(stored)["services"]), {"api", "analytics"})

            code, out = run("analytics", ANALYTICS.replace(INTERNAL, "x" * 40), "--compare", path)
            self.assertEqual(code, 1)
            self.assertIn("FAIL  INTERNAL_JWT_SECRET identical on api and analytics", out)
            code, out = run("analytics", ANALYTICS.replace(INTERNAL, JWT), "--compare", path)
            self.assertIn("FAIL  analytics INTERNAL_JWT_SECRET differs from api JWT_SECRET", out)

    def test_values_with_equals_signs_and_continuation_lines(self):
        env = preflight.parse_kv("A=x=y\nB=line1\nline2\nC=\n")
        self.assertEqual(env, {"A": "x=y", "B": "line1\nline2", "C": ""})


if __name__ == "__main__":
    unittest.main()
