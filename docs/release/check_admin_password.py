#!/usr/bin/env python3
"""Say whether one bcrypt hash (read from stdin) is the hash of "admin123".

    psql ... -Atc "SELECT password FROM users WHERE id = <id>" | python3 check_admin_password.py

Prints MATCH or NO MATCH and nothing else; never echoes the hash.
Exit codes: 0 = no match, 1 = match (the account must be fixed), 2 = not a bcrypt hash.
Python 3 standard library only: bcrypt is implemented below (verify only, $2a$/$2b$/$2y$).
"""

import hmac
import re
import sys

CANDIDATE = b"admin123"

_B64 = "./ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
_HASH = re.compile(r"^\$2[aby]\$(\d\d)\$([./A-Za-z0-9]{22})([./A-Za-z0-9]{31})$")
_M32 = 0xFFFFFFFF


def _pi_words(n: int) -> list[int]:
    """The first n 32-bit words of pi's fractional part: Blowfish's initial P-array and S-boxes."""
    guard = 64
    one = 1 << (32 * n + guard)

    def arctan_inv(x: int) -> int:
        total = term = one // x
        x2, k, sign = x * x, 1, -1
        while term:
            term //= x2
            k += 2
            total += sign * (term // k)
            sign = -sign
        return total

    frac = (16 * arctan_inv(5) - 4 * arctan_inv(239) - 3 * one) >> guard
    return [(frac >> (32 * (n - 1 - i))) & _M32 for i in range(n)]


_INIT = _pi_words(18 + 4 * 256)
assert _INIT[0] == 0x243F6A88 and _INIT[18] == 0xD1310BA6, "Blowfish constants"


def _b64decode(s: str, nbytes: int) -> bytes:
    bits = 0
    nbits = 0
    out = bytearray()
    for ch in s:
        bits = (bits << 6) | _B64.index(ch)
        nbits += 6
        if nbits >= 8:
            nbits -= 8
            out.append((bits >> nbits) & 0xFF)
    return bytes(out[:nbytes])


def _b64encode(data: bytes) -> str:
    out = []
    for i in range(0, len(data), 3):
        chunk = data[i:i + 3]
        n = int.from_bytes(chunk.ljust(3, b"\0"), "big")
        out.extend(_B64[(n >> s) & 63] for s in (18, 12, 6, 0))
        if len(chunk) < 3:
            del out[len(chunk) - 3:]
    return "".join(out)


def _words(data: bytes, count: int) -> list[int]:
    """count 32-bit words taken cyclically from data (Blowfish's stream2word)."""
    out, j = [], 0
    for _ in range(count):
        w = 0
        for _ in range(4):
            w = (w << 8) | data[j]
            j = (j + 1) % len(data)
        out.append(w)
    return out


def _encrypt(p, s0, s1, s2, s3, left, right):
    for i in range(0, 16, 2):
        left ^= p[i]
        right ^= ((((s0[left >> 24] + s1[(left >> 16) & 0xFF]) & _M32) ^ s2[(left >> 8) & 0xFF]) + s3[left & 0xFF]) & _M32
        right ^= p[i + 1]
        left ^= ((((s0[right >> 24] + s1[(right >> 16) & 0xFF]) & _M32) ^ s2[(right >> 8) & 0xFF]) + s3[right & 0xFF]) & _M32
    return right ^ p[17], left ^ p[16]


def _expand(p, sboxes, key_words, salt_words):
    """Blowfish key schedule; with salt_words it is bcrypt's salted ExpandKey."""
    for i in range(18):
        p[i] ^= key_words[i]
    s0, s1, s2, s3 = sboxes
    left = right = 0
    j = 0
    for box in (p, s0, s1, s2, s3):
        for i in range(0, len(box), 2):
            if salt_words:
                left ^= salt_words[j]
                right ^= salt_words[j + 1]
                j = (j + 2) % 4
            left, right = _encrypt(p, s0, s1, s2, s3, left, right)
            box[i], box[i + 1] = left, right


def bcrypt_hash(password: bytes, cost: int, salt: bytes) -> bytes:
    """The 23-byte bcrypt digest of password with this cost and 16-byte salt."""
    key = (password + b"\0")[:72]
    key_words = _words(key, 18)
    salt_words = _words(salt, 4)
    salt_key = _words(salt, 18)
    p = _INIT[:18]
    sboxes = [_INIT[18 + 256 * k: 18 + 256 * (k + 1)] for k in range(4)]
    _expand(p, sboxes, key_words, salt_words)
    for _ in range(1 << cost):
        _expand(p, sboxes, key_words, None)
        _expand(p, sboxes, salt_key, None)
    s0, s1, s2, s3 = sboxes
    text = _words(b"OrpheanBeholderScryDoubt", 6)
    for _ in range(64):
        for i in range(0, 6, 2):
            text[i], text[i + 1] = _encrypt(p, s0, s1, s2, s3, text[i], text[i + 1])
    return b"".join(w.to_bytes(4, "big") for w in text)[:23]


def matches(password: bytes, stored: str) -> bool:
    m = _HASH.match(stored)
    if not m:
        raise ValueError("not a bcrypt hash")
    cost, salt, digest = int(m.group(1)), m.group(2), m.group(3)
    if not 4 <= cost <= 31:
        raise ValueError("bcrypt cost out of range")
    computed = _b64encode(bcrypt_hash(password, cost, _b64decode(salt, 16)))
    return hmac.compare_digest(computed, digest)


def main() -> int:
    stored = sys.stdin.read().strip()
    try:
        found = matches(CANDIDATE, stored)
    except ValueError as e:
        print(f"ERROR: input is {e} (expected one $2a$/$2b$/$2y$ hash on stdin)")
        return 2
    print("MATCH: this hash is for \"admin123\"" if found else "NO MATCH")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
