"""One-cycle acquisition worker. No contract acceptance or unverified publication.

Uses already-configured Core authentication and feeds. Can run from an external
scheduler without copying credentials into GitHub.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request


def core_request(path: str, *, payload: dict | None = None) -> dict:
    base = os.environ["CORE_URL"].rstrip("/")
    if not base.startswith("https://"):
        raise ValueError("CORE_URL must be HTTPS")
    headers = {"x-core-ingest-key": os.environ["CORE_INGEST_KEY"],
               "Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        base + path,
        data=json.dumps(payload).encode("utf-8") if payload is not None else None,
        headers=headers,
        method="POST" if payload is not None else "GET",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.load(response)


def run_once() -> dict:
    # Discovery is independent of the two previously considered advertisers.
    discovery = core_request("/v1/awin/discovery/alternatives?region=BR&limit=100")
    # Importing candidates does not require advertiser approval. Commercial
    # publication remains gated by independently verified permissions.
    ingestion = core_request("/v1/awin/import-multiple", payload={
        "dry_run": False, "max_rows": 10000,
    })
    return {
        "regional_alternatives": discovery.get("regional_alternatives", 0),
        "joined_alternatives": discovery.get("joined_alternatives", 0),
        "feeds_processed": ingestion.get("successful_sources", 0),
        "candidate_records_imported": ingestion.get("imported", 0),
        "publication_claimed": False,
    }


if __name__ == "__main__":
    print(json.dumps(run_once(), ensure_ascii=False))
