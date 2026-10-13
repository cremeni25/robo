"""Scheduled Awin inbox sync with refreshable OAuth credentials.

Required environment variables:
GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN,
CORE_URL, CORE_INGEST_KEY.

Run periodically as a dedicated Render cron job, not as a web startup hook.
Never print OAuth credentials or invitation contents.
"""
import json
import os
import urllib.parse
import urllib.request

from core_v1.app.awin_gmail_adapter import sync_once


def refresh_gmail_access_token() -> str:
    required = ("GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET", "GMAIL_REFRESH_TOKEN")
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise RuntimeError("Missing Gmail OAuth configuration: " + ", ".join(missing))
    form = urllib.parse.urlencode({
        "client_id": os.environ["GMAIL_CLIENT_ID"],
        "client_secret": os.environ["GMAIL_CLIENT_SECRET"],
        "refresh_token": os.environ["GMAIL_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        data = json.load(response)
    token = data.get("access_token")
    if not token:
        raise RuntimeError("Gmail OAuth token refresh did not return an access token")
    return token


def main() -> dict:
    return sync_once(
        gmail_token=refresh_gmail_access_token(),
        core_url=os.environ["CORE_URL"],
        core_key=os.environ["CORE_INGEST_KEY"],
    )


if __name__ == "__main__":
    result = main()
    print(json.dumps(result, sort_keys=True))
