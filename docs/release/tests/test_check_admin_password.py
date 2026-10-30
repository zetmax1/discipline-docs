"""Vectors generated with golang.org/x/crypto/bcrypt, the library the API hashes with."""

import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import check_admin_password as cap  # noqa: E402

ADMIN123_COST10 = "$2a$10$JKHj0pnNEh5vDhBXTGDu/u09Fzgl7n.h.e9wE6vw9SnK7AdsgratO"
ADMIN1234_COST10 = "$2a$10$Vn/ag0vnQeWw0DIpAyjQm.fb6R90kJszwAclYN3fdEw8ZTLir82ny"
VECTORS_COST4 = {
    b"admin123": "$2a$04$9f.M38jfboFXa8QrnG15/Ou9CYBaoAQ9pHL/TcQQAUbFhm/2.ftLO",
    b"Admin123": "$2a$04$PDTToYLxauqgU00SbW45uONLeE9cOREhi3mtEHMS97.G/j5FUh19S",
    b"": "$2a$04$3DaktpZeHYRn48KumscUZ.O0E6wj0R8iTMhFlDL1bU65a4KLDpbYC",
}


def cli(stdin: str):
    r = subprocess.run([sys.executable, "-I", str(HERE / "check_admin_password.py")],
                       input=stdin, capture_output=True, text=True)
    return r.returncode, r.stdout


class CheckAdminPasswordTest(unittest.TestCase):
    def test_go_vectors(self):
        for password, stored in VECTORS_COST4.items():
            self.assertTrue(cap.matches(password, stored), password)
            self.assertFalse(cap.matches(password + b"x", stored), password)

    def test_2b_and_2y_prefixes(self):
        stored = VECTORS_COST4[b"admin123"]
        for prefix in ("$2b$", "$2y$"):
            self.assertTrue(cap.matches(b"admin123", prefix + stored[4:]))

    def test_cli_match_no_match_and_bad_input(self):
        code, out = cli(ADMIN123_COST10 + "\n")
        self.assertEqual((code, out), (1, 'MATCH: this hash is for "admin123"\n'))
        code, out = cli(ADMIN1234_COST10)
        self.assertEqual((code, out), (0, "NO MATCH\n"))
        code, out = cli("$2a$10$tooshort")
        self.assertEqual(code, 2)
        self.assertNotIn("tooshort", out)


if __name__ == "__main__":
    unittest.main()
