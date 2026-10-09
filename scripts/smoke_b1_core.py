"""Read-only smoke tests for ROBÔ GLOBAL public B1/Core integration.

Run: python scripts/smoke_b1_core.py
No writes, purchases, clicks, personal data, or artificial conversions.
"""
import json
import sys
import urllib.error
import urllib.request

API = "https://robo-global-api-v2.onrender.com"
CORE = "https://robo-global-core-v1.onrender.com"

def check(url, expected_status, validate=None):
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "RoboGlobal-ReadOnlySmoke/1"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            status = response.status
            body = response.read(262144)
    except urllib.error.HTTPError as error:
        status = error.code
        body = error.read(262144)
    except (urllib.error.URLError, TimeoutError) as error:
        raise AssertionError(f"{url}: network unavailable: {error}") from error
    assert status == expected_status, f"{url}: expected {expected_status}, got {status}: {body[:250]!r}"
    if validate is not None:
        validate(json.loads(body))
    print(f"PASS {status} {url}")

def check_catalog(data):
    assert isinstance(data, dict) and data.get("status") == "OK"
    assert isinstance(data.get("data"), list)
    assert data.get("total") == len(data["data"])
    assert all(isinstance(row.get("slug"), str) and row.get("title") for row in data["data"])

def main():
    check(API + "/status", 200)
    check(API + "/public/nichos", 200, check_catalog)
    # A non-UUID legacy GUL must never redirect to a merchant.
    check(API + "/go/legacy-smoke-invalid", 503)
    # An unknown UUID can be routed to Core, but must not create a click or redirect to a merchant.
    check(CORE + "/r/00000000-0000-4000-8000-000000000000", 404)
    print("Read-only B1/Core smoke checks passed; commercial sales NOT certified.")

if __name__ == "__main__":
    try:
        main()
    except (AssertionError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
