"""Read-only smoke tests for ROBÔ GLOBAL public B1/Core integration.

Run: python scripts/smoke_b1_core.py
No writes, purchases, clicks, personal data, or artificial conversions.
"""
import json
import sys
import urllib.error
import urllib.request
from urllib.parse import quote

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
    return json.loads(body) if body else None

def check_catalog(data):
    assert isinstance(data, dict) and data.get("status") == "OK"
    assert isinstance(data.get("data"), list)
    assert data.get("total") == len(data["data"])
    assert all(isinstance(row.get("slug"), str) and row.get("title") for row in data["data"])

def check_offers(data):
    assert isinstance(data, dict) and data.get("status") == "OK"
    assert isinstance(data.get("data"), list)
    assert data.get("total") == len(data["data"])
    for item in data["data"]:
        assert item["url"] == "/go/" + item["id"], "untracked external URL exposed"

def check_offers_core(data):
    assert isinstance(data, dict) and data.get("status") == "OK"
    assert isinstance(data.get("data"), list)
    assert data.get("total") == len(data["data"])
    for item in data["data"]:
        assert item["url"] == "/r/" + item["id"], "noncanonical Core redirect"

def main():
    check(API + "/status", 200)
    niches = check(API + "/public/nichos", 200, check_catalog)
    check(CORE + "/v1/public/catalog", 200, check_offers_core)
    check(API + "/public/ofertas", 200, check_offers)
    # A non-UUID legacy GUL must never redirect to a merchant.
    check(API + "/go/legacy-smoke-invalid", 503)
    # An unknown UUID can be routed to Core, but must not create a click or redirect to a merchant.
    check(CORE + "/r/00000000-0000-4000-8000-000000000000", 404)
    check(CORE + "/v1/public/catalog/by-need/not-a-uuid", 422)
    check(API + "/public/dores/00000000-0000-4000-8000-000000000000/solucoes", 404)
    needs = 0
    matches = 0
    for niche in niches["data"]:
        subs = check(API + "/public/nichos/" + quote(niche["slug"]) + "/subnichos", 200, check_catalog)
        for sub in subs["data"]:
            pains = check(API + "/public/subnichos/" + sub["id"] + "/dores", 200, check_catalog)
            for need in pains["data"]:
                linked = check(API + "/public/dores/" + need["id"] + "/solucoes", 200, check_offers_core)
                core = check(CORE + "/v1/public/catalog/by-need/" + need["id"], 200, check_offers_core)
                assert linked == core, "V2/Core mapping diverged"
                needs += 1
                matches += linked["total"]
                print(f"VERIFIED need={need['id']} matches={linked['total']}")
    print(f"Verified {needs} real published needs and {matches} eligible matches.")
    print("Read-only B1/Core smoke checks passed; commercial sales NOT certified.")

if __name__ == "__main__":
    try:
        main()
    except (AssertionError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
