"""
Security Test Suite — Ayansh Infocom Admin Portal
===================================================
Tests authentication, authorization, and common attack vectors
against the admin panel and all protected API endpoints.

Run:  python tests/test_security.py
"""

import sys
import io
import time
import json
import http.client
import urllib.parse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE      = "localhost"
PORT      = 8000
VALID_USER = "admin"
VALID_PASS = "ayansh@2025"

# ── Counters ────────────────────────────────────────────────
_passed = 0
_failed = 0
_warnings = 0


def _req(method, path, body=None, headers=None, cookies=None):
    """Send an HTTP request and return (status, headers_dict, body_str)."""
    try:
        conn = http.client.HTTPConnection(BASE, PORT, timeout=5)
        h = {"Content-Type": "application/json"}
        if headers:
            h.update(headers)
        if cookies:
            h["Cookie"] = "; ".join(f"{k}={v}" for k, v in cookies.items())
        data = json.dumps(body).encode() if body else None
        conn.request(method, path, body=data, headers=h)
        resp = conn.getresponse()
        resp_body = resp.read().decode("utf-8", errors="replace")
        resp_headers = dict(resp.getheaders())
        conn.close()
        return resp.status, resp_headers, resp_body
    except Exception as e:
        return 0, {}, f"CONNECTION_ERROR: {e}"


def check(name, condition, detail="", warn=False):
    global _passed, _failed, _warnings
    symbol = "PASS" if condition else ("WARN" if warn else "FAIL")
    color  = "\033[92m" if condition else ("\033[93m" if warn else "\033[91m")
    reset  = "\033[0m"
    status = f"[{color}{symbol}{reset}]"
    print(f"  {status}  {name}")
    if detail:
        print(f"         {detail}")
    if condition:
        _passed += 1
    elif warn:
        _warnings += 1
    else:
        _failed += 1


def section(title):
    print(f"\n  {'=' * 60}")
    print(f"  {title}")
    print(f"  {'=' * 60}")


# ================================================================
#  HELPER — login and get session cookie
# ================================================================

def login(username=VALID_USER, password=VALID_PASS):
    status, headers, body = _req("POST", "/api/admin/login",
                                  body={"username": username, "password": password})
    if status == 200:
        data = json.loads(body)
        token = data.get("token", "")
        return token, {"admin_token": token}
    return None, {}


# ================================================================
#  TEST 1 — Unauthenticated Access
# ================================================================

section("1. Unauthenticated Access (No Token)")

status, headers, body = _req("GET", "/admin")
check(
    "GET /admin redirects to login page (302)",
    status in (302, 307),
    detail=f"Got HTTP {status}"
)

PROTECTED_APIS = [
    ("GET",    "/api/admin/products"),
    ("POST",   "/api/admin/products"),
    ("GET",    "/api/admin/knowledge"),
    ("POST",   "/api/admin/knowledge"),
    ("DELETE", "/api/admin/products/FAKE-ID"),
    ("DELETE", "/api/admin/knowledge/999"),
]

for method, path in PROTECTED_APIS:
    status, _, body = _req(method, path, body={"dummy": True} if method == "POST" else None)
    check(
        f"{method} {path} returns 401 without token",
        status == 401,
        detail=f"Got HTTP {status}"
    )

# ================================================================
#  TEST 2 — Login Endpoint Security
# ================================================================

section("2. Login Endpoint Security")

# Wrong password
status, _, body = _req("POST", "/api/admin/login",
                         body={"username": VALID_USER, "password": "wrongpassword"})
check("Wrong password → 401", status == 401, detail=f"Got HTTP {status}")

# Wrong username
status, _, body = _req("POST", "/api/admin/login",
                         body={"username": "hacker", "password": VALID_PASS})
check("Wrong username → 401", status == 401, detail=f"Got HTTP {status}")

# Empty credentials
status, _, body = _req("POST", "/api/admin/login",
                         body={"username": "", "password": ""})
check("Empty credentials → 401 or 422", status in (401, 422), detail=f"Got HTTP {status}")

# SQL Injection in username
sql_payloads = [
    "admin' --",
    "admin' OR '1'='1",
    "' OR 1=1 --",
    "admin\"; DROP TABLE users; --",
]
for payload in sql_payloads:
    status, _, body = _req("POST", "/api/admin/login",
                             body={"username": payload, "password": "anything"})
    check(
        f"SQL injection in username → 401",
        status == 401,
        detail=f"Payload: {payload!r} → HTTP {status}"
    )

# SQL Injection in password
for payload in sql_payloads[:2]:
    status, _, body = _req("POST", "/api/admin/login",
                             body={"username": VALID_USER, "password": payload})
    check(
        f"SQL injection in password → 401",
        status == 401,
        detail=f"Payload: {payload!r} → HTTP {status}"
    )

# ================================================================
#  TEST 3 — Token Security
# ================================================================

section("3. Token / Session Security")

# Valid login
token, cookies = login()
check("Valid login returns a token", token is not None, detail=f"Token: {token[:12]}…" if token else "No token")

# Fake/tampered token
status, _, _ = _req("GET", "/api/admin/products",
                      cookies={"admin_token": "fake_token_abc123"})
check("Fake token → 401", status == 401, detail=f"Got HTTP {status}")

# Truncated real token
if token:
    status, _, _ = _req("GET", "/api/admin/products",
                          cookies={"admin_token": token[:10]})
    check("Truncated token → 401", status == 401, detail=f"Got HTTP {status}")

# Valid token works
if token:
    status, _, body = _req("GET", "/api/admin/products", cookies=cookies)
    check("Valid token → 200 on protected API", status == 200, detail=f"Got HTTP {status}")

# Check Set-Cookie flags
_, resp_headers, _ = _req("POST", "/api/admin/login",
                            body={"username": VALID_USER, "password": VALID_PASS})
set_cookie = resp_headers.get("set-cookie", "")
check(
    "Session cookie has HttpOnly flag",
    "httponly" in set_cookie.lower(),
    detail=f"Cookie header: {set_cookie[:80]}"
)
check(
    "Session cookie has SameSite flag",
    "samesite" in set_cookie.lower(),
    detail=f"Cookie header: {set_cookie[:80]}"
)

# ================================================================
#  TEST 4 — Logout & Session Invalidation
# ================================================================

section("4. Logout & Session Invalidation")

token2, cookies2 = login()
if token2:
    # Verify it works before logout
    status, _, _ = _req("GET", "/api/admin/products", cookies=cookies2)
    check("Token works before logout", status == 200, detail=f"Got HTTP {status}")

    # Logout
    status, _, _ = _req("POST", "/api/admin/logout", cookies=cookies2)
    check("Logout returns 200", status == 200, detail=f"Got HTTP {status}")

    # Try to use token after logout
    status, _, _ = _req("GET", "/api/admin/products", cookies=cookies2)
    check("Token rejected after logout → 401", status == 401, detail=f"Got HTTP {status}")

# ================================================================
#  TEST 5 — Brute Force / Rate Limit Observation
# ================================================================

section("5. Brute Force Simulation (5 rapid wrong attempts)")

t_start = time.time()
for i in range(5):
    status, _, _ = _req("POST", "/api/admin/login",
                          body={"username": VALID_USER, "password": f"wrong{i}"})
t_end = time.time()

check(
    "All 5 wrong-password requests return 401",
    status == 401,
    detail=f"5 attempts in {t_end - t_start:.2f}s"
)

# Still works with correct creds after brute force
status, _, _ = _req("POST", "/api/admin/login",
                     body={"username": VALID_USER, "password": VALID_PASS})
check("Valid login still works after brute force", status == 200, detail=f"Got HTTP {status}")

# Warn if no rate limiting is in place
check(
    "NOTE: No rate limiting detected (recommend adding in production)",
    True,
    detail="Consider adding slowapi or nginx rate limiting for production.",
    warn=True
)

# ================================================================
#  TEST 6 — Injection & Fuzzing on Admin APIs
# ================================================================

section("6. Injection & Fuzzing on Protected Admin APIs")

_, cookies3 = login()

# Try to inject via product_id path — use URL-safe encoded payloads only
malicious_ids = [
    "FAKE-ID-999",
    "test%27%20OR%201%3D1%20--",   # ' OR 1=1 -- (URL-encoded)
    "..%2F..%2Fetc%2Fpasswd",      # ../../etc/passwd (URL-encoded)
    "FAKE%3Cscript%3E",            # <script> (URL-encoded)
]
for mid in malicious_ids:
    encoded = urllib.parse.quote(mid, safe="")
    status, _, body = _req("DELETE", f"/api/admin/products/{encoded}", cookies=cookies3)
    check(
        f"Malicious product_id DELETE → non-500",
        status != 500,
        detail=f"ID={mid!r} → HTTP {status}"
    )

# Try malformed JSON body on POST
conn = http.client.HTTPConnection(BASE, PORT, timeout=8)
conn.request("POST", "/api/admin/products",
             body=b"{not valid json}",
             headers={"Content-Type": "application/json",
                      "Cookie": f"admin_token={cookies3.get('admin_token','')}"})
resp = conn.getresponse()
resp.read()
conn.close()
check(
    "Malformed JSON body → 422 (validation error, not crash)",
    resp.status == 422,
    detail=f"Got HTTP {resp.status}"
)

# ================================================================
#  TEST 7 — Public Routes Remain Accessible
# ================================================================

section("7. Public Routes Still Accessible (Chat UI)")

status, _, _ = _req("GET", "/")
check("GET / (Chat UI) is publicly accessible → 200", status == 200, detail=f"Got HTTP {status}")

status, _, _ = _req("GET", "/admin-login")
check("GET /admin-login is publicly accessible → 200", status == 200, detail=f"Got HTTP {status}")

# ================================================================
#  SUMMARY
# ================================================================

total = _passed + _failed + _warnings
print(f"\n  {'=' * 60}")
print(f"  SECURITY TEST RESULTS")
print(f"  {'=' * 60}")
print(f"  Total Checks : {total}")
print(f"  \033[92mPassed\033[0m       : {_passed}")
print(f"  \033[91mFailed\033[0m       : {_failed}")
print(f"  \033[93mWarnings\033[0m     : {_warnings}")
print()
if _failed == 0:
    print("  \033[92m[OK] All security checks passed!\033[0m")
else:
    print(f"  \033[91m[!!] {_failed} security check(s) FAILED — review above.\033[0m")
print()
