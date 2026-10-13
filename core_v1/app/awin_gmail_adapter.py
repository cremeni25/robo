"""Privacy-minimizing adapter for Awin invitation notifications.

Run this worker with a dedicated Gmail OAuth token and Core ingestion key.
No email bodies, invitation URLs, or personal addresses are forwarded to Core.
"""
from __future__ import annotations

import base64
import json
import os
import re
import urllib.parse
import urllib.request

GMAIL_API = "https://gmail.googleapis.com/gmail/v1/users/me"
AWIN_SENDERS = {"no-reply@awin.com", "help@awin.com"}
INVITE_TERMS = ("convidou você para fazer parte de seu programa", "invited you to join", "invitation to join")
PROGRAM_RE = re.compile(r"/membership-invitation/accept/\\d+/(\\d+)(?:/|\\?)")
NAME_RE = re.compile(r"^(.{2,150}?) (?:convidou você|invited you)", re.I)


def _request(url: str, token: str) -> dict:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)


def _decode(part: dict) -> str:
    data = part.get("body", {}).get("data")
    if data:
        return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", "replace")
    return "\n".join(_decode(p) for p in part.get("parts", []))


def parse_invitation(message: dict) -> dict | None:
    headers = {h.get("name", "").lower(): h.get("value", "") for h in message.get("payload", {}).get("headers", [])}
    sender = headers.get("from", "").lower()
    if not any(f"<{allowed}>" in sender or sender.strip() == allowed for allowed in AWIN_SENDERS):
        return None
    subject = headers.get("subject", "")
    body = _decode(message.get("payload", {}))
    if not any(term in (subject + " " + body).lower() for term in INVITE_TERMS):
        return None
    match = PROGRAM_RE.search(urllib.parse.unquote(body))
    advertiser = NAME_RE.search(subject)
    if not advertiser:
        return None
    return {
        "external_event_id": "gmail:" + message["id"],
        "advertiser": advertiser.group(1).strip(),
        "terms_available": bool(re.search(r"terms.and.conditions|termos.e.condi", body, re.I)),
        "program_id_for_local_audit": match.group(1) if match else None,
    }


def sync_once(*, gmail_token: str, core_url: str, core_key: str) -> dict:
    if not core_url.startswith("https://"):
        raise ValueError("Core HTTPS URL required")
    query = urllib.parse.urlencode({"q": "newer_than:14d (from:no-reply@awin.com OR from:help@awin.com)", "maxResults": 100})
    listing = _request(f"{GMAIL_API}/messages?{query}", gmail_token)
    count = 0
    for item in listing.get("messages", []):
        message = _request(f"{GMAIL_API}/messages/{item['id']}?format=full", gmail_token)
        signal = parse_invitation(message)
        if not signal:
            continue
        signal.pop("program_id_for_local_audit", None)
        payload = json.dumps(signal).encode("utf-8")
        req = urllib.request.Request(
            core_url.rstrip("/") + "/v1/awin/discovery/invitation-ingest",
            data=payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {core_key}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            if response.status != 200:
                raise RuntimeError("Core ingestion rejected")
        count += 1
    return {"processed": count, "publication_enabled": False}


if __name__ == "__main__":
    print(json.dumps(sync_once(
        gmail_token=os.environ["GMAIL_ACCESS_TOKEN"],
        core_url=os.environ["CORE_URL"],
        core_key=os.environ["CORE_INGEST_KEY"],
    )))
