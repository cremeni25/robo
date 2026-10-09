"""Discover Awin advertisers safely. Never approves offers or publishes links."""
import json
import os
from urllib.request import Request, urlopen


def discover(fetch=urlopen, environment=None):
    env = os.environ if environment is None else environment
    token = env.get("AWIN_API_TOKEN", "").strip()
    publisher = env.get("AWIN_PUBLISHER_ID", "").strip()
    if not token or not publisher.isdigit():
        return {"status": "configuration_required", "advertiser_count": 0}

    endpoint = f"https://api.awin.com/publishers/{publisher}/programmes"
    request = Request(endpoint, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/json",
    })
    with fetch(request, timeout=25) as response:
        payload = json.load(response)
    records = payload.get("programmes", payload.get("data", [])) if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise ValueError("Unexpected Awin response")
    statuses = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        relation = record.get("membershipStatus", record.get("relationship", "unknown"))
        if isinstance(relation, dict):
            relation = relation.get("status", "unknown")
        key = str(relation).strip().lower()
        statuses[key] = statuses.get(key, 0) + 1
    return {
        "status": "discovered",
        "advertiser_count": len(records),
        "relationship_counts": statuses,
        "relationship_status_verified": all(k != "unknown" for k in statuses),
        "offers_published": 0,
        "commercial_approval_automated": False,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(discover(), ensure_ascii=False))
    except Exception as exc:
        # Do not leak HTTP errors, tokens or URLs into logs.
        print(json.dumps({"status": "discovery_failed", "error_type": type(exc).__name__}))
        raise SystemExit(1)
