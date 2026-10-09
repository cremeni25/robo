"""Awin read-only integration primitives. No program enrollment or publication.

Credentials must be supplied by secure server environment, never embedded in URLs
shown to users. A feed being downloadable is NOT evidence of commission eligibility.
"""
from __future__ import annotations

import csv
import gzip
import io
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class AwinError(ValueError):
    pass


@dataclass(frozen=True)
class AwinOffer:
    merchant_id: str
    product_id: str
    name: str
    price: Decimal | None
    currency: str
    affiliate_url: str
    raw: dict[str, str]
    eligibility: str = "unverified"

    @property
    def publishable(self) -> bool:
        return self.eligibility == "verified"


def _price(value: str | None) -> Decimal | None:
    if not value:
        return None
    try:
        return Decimal(str(value).strip().replace(",", "."))
    except (InvalidOperation, ValueError):
        return None


def parse_feed(content: bytes, *, compressed: bool = True, max_rows: int = 100000) -> list[AwinOffer]:
    """Parse either Awin legacy or Google-format CSV; retain source evidence."""
    if compressed:
        content = gzip.decompress(content)
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig"), newline=""))
    if not reader.fieldnames:
        raise AwinError("missing CSV header")
    offers: list[AwinOffer] = []
    for i, row in enumerate(reader):
        if i >= max_rows:
            raise AwinError("feed exceeds configured row limit")
        record = {str(k): str(v or "") for k, v in row.items() if k is not None}
        merchant = record.get("merchant_id") or record.get("advertiser_id") or record.get("aw_merchant_id") or ""
        product = record.get("aw_product_id") or record.get("id") or record.get("merchant_product_id") or ""
        name = record.get("product_name") or record.get("title") or ""
        link = record.get("aw_deep_link") or record.get("link") or ""
        if not (merchant and product and name and link):
            continue
        parsed = urlparse(link)
        if parsed.scheme != "https" or not parsed.hostname:
            continue
        offers.append(AwinOffer(
            merchant_id=merchant, product_id=product, name=name,
            price=_price(record.get("search_price") or record.get("price")),
            currency=(record.get("currency") or "BRL").upper(),
            affiliate_url=link, raw=record,
        ))
    return offers


def eligibility_for_program(program: dict[str, Any], *, has_feed: bool = False,
                            soft_membership_verified: bool = False,
                            terms_reviewed: bool = False) -> str:
    """Fail closed: status, soft membership and permitted channels must be proven."""
    status = str(program.get("membershipStatus") or program.get("membership_status") or "").lower()
    if not terms_reviewed:
        return "terms_unverified"
    if program.get("channel_permitted") is not True:
        return "channel_unverified"
    if status in {"joined", "approved", "active"}:
        return "verified"
    if has_feed and soft_membership_verified and program.get("soft_membership_allowed") is True:
        return "verified"
    return "not_authorized"


class AwinClient:
    """Read-only Publisher API access. No enrollment or state-changing methods."""
    BASE = "https://api.awin.com"

    def __init__(self, publisher_id: int, token: str):
        if publisher_id <= 0 or not token:
            raise AwinError("publisher ID and API token required")
        self.publisher_id = publisher_id
        self._token = token

    def get(self, path: str) -> Any:
        if not path.startswith("/") or "://" in path:
            raise AwinError("invalid API path")
        request = Request(
            self.BASE + path,
            headers={"Authorization": "Bearer " + self._token, "Accept": "application/json"},
            method="GET",
        )
        with urlopen(request, timeout=25) as response:
            return json.load(response)

    def programs(self, membership: str = "all") -> Any:
        if membership not in {"all", "joined", "notjoined"}:
            raise AwinError("invalid membership filter")
        return self.get(f"/publishers/{self.publisher_id}/programmes" + (f"?relationship={membership}" if membership != "all" else ""))

    def program_details(self) -> Any:
        return self.get(f"/publishers/{self.publisher_id}/programmedetails")
