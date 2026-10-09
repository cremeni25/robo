from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any


APPROVED_EVENTS = {
    "PURCHASE_APPROVED",
    "PURCHASE_COMPLETE",
}
REFUND_EVENTS = {
    "PURCHASE_REFUNDED",
    "PURCHASE_PARTIALLY_REFUNDED",
}
CHARGEBACK_EVENTS = {
    "PURCHASE_CHARGEBACK",
}
CANCELLED_EVENTS = {
    "PURCHASE_CANCELED",
    "PURCHASE_CANCELLED",
}
PENDING_EVENTS = {
    "PURCHASE_BILLET_PRINTED",
    "PURCHASE_DELAYED",
    "PURCHASE_PROTEST",
    "PURCHASE_WAITING_PAYMENT",
}


@dataclass(frozen=True)
class HotmartConversion:
    external_event_id: str | None
    event_type: str
    external_sale_id: str | None
    external_product_id: str | None
    attribution_key: str | None
    gross_value: Decimal
    commission_value: Decimal
    currency: str
    status: str | None
    occurred_at_ms: int | None


def _decimal(value: Any) -> Decimal:
    try:
        if value is None:
            return Decimal("0")
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def _first(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _sum_affiliate_commissions(data: dict[str, Any]) -> Decimal:
    commissions = data.get("commissions") or data.get("commission") or []
    if isinstance(commissions, dict):
        direct = _first(commissions.get("value"), commissions.get("amount"))
        if direct is not None:
            return _decimal(direct)
        commissions = [commissions]

    total = Decimal("0")
    if isinstance(commissions, list):
        for item in commissions:
            if not isinstance(item, dict):
                continue
            source = str(_first(item.get("source"), item.get("role"), item.get("type")) or "").upper()
            if source and "AFFILIATE" not in source:
                continue
            value = _first(
                item.get("value"),
                item.get("amount"),
                (item.get("commission") or {}).get("value") if isinstance(item.get("commission"), dict) else None,
            )
            total += _decimal(value)
    return total


def normalize_status(event_type: str) -> str | None:
    event = event_type.upper()
    if event in APPROVED_EVENTS:
        return "approved"
    if event in REFUND_EVENTS:
        return "refunded"
    if event in CHARGEBACK_EVENTS:
        return "chargeback"
    if event in CANCELLED_EVENTS:
        return "cancelled"
    if event in PENDING_EVENTS:
        return "pending"
    return None


def validate_hottok(received: str | None, expected: str | None) -> bool:
    if not expected:
        return False
    return bool(received) and received == expected


def normalize_webhook(payload: dict[str, Any]) -> HotmartConversion:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    purchase = data.get("purchase") if isinstance(data.get("purchase"), dict) else {}
    product = data.get("product") if isinstance(data.get("product"), dict) else {}
    tracking = purchase.get("tracking") if isinstance(purchase.get("tracking"), dict) else {}
    price = purchase.get("price") if isinstance(purchase.get("price"), dict) else {}

    event_type = str(_first(payload.get("event"), payload.get("event_type"), "UNKNOWN")).upper()
    external_event_id = _first(payload.get("id"), payload.get("event_id"))
    transaction = _first(purchase.get("transaction"), data.get("transaction"), payload.get("transaction"))
    product_id = _first(product.get("id"), product.get("ucode"), data.get("product_id"))

    attribution_key = _first(
        tracking.get("source"),
        tracking.get("source_sck"),
        tracking.get("external_code"),
        purchase.get("sales_source"),
        data.get("sales_source"),
    )

    gross_value = _decimal(_first(price.get("value"), purchase.get("full_price"), data.get("price")))
    currency = str(_first(price.get("currency_code"), purchase.get("currency"), data.get("currency"), "BRL")).upper()
    commission_value = _sum_affiliate_commissions(data)
    occurred_at_ms = _first(
        payload.get("creation_date"),
        purchase.get("approved_date"),
        purchase.get("order_date"),
    )
    try:
        occurred_at_ms = int(occurred_at_ms) if occurred_at_ms is not None else None
    except (TypeError, ValueError):
        occurred_at_ms = None

    return HotmartConversion(
        external_event_id=str(external_event_id) if external_event_id is not None else None,
        event_type=event_type,
        external_sale_id=str(transaction) if transaction is not None else None,
        external_product_id=str(product_id) if product_id is not None else None,
        attribution_key=str(attribution_key) if attribution_key is not None else None,
        gross_value=gross_value,
        commission_value=commission_value,
        currency=currency,
        status=normalize_status(event_type),
        occurred_at_ms=occurred_at_ms,
    )
