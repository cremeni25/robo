# sales_service.py
from supabase import Client
from decimal import Decimal
from datetime import datetime


def registrar_venda(
    supabase: Client,
    *,
    platform: str,
    external_sale_id: str,
    product_id: str,
    partner_id: str | None,
    gross_value: Decimal,
    commission_value: Decimal,
    partner_commission: Decimal,
    master_commission: Decimal,
    sale_status: str,
    occurred_at: datetime,
    payload: dict
):
    data = {
        "platform": platform,
        "external_sale_id": external_sale_id,
        "product_id": product_id,
        "partner_id": partner_id,
        "gross_value": gross_value,
        "commission_value": commission_value,
        "partner_commission": partner_commission,
        "master_commission": master_commission,
        "sale_status": sale_status,
        "occurred_at": occurred_at.isoformat(),
        "event_payload": payload,
    }

    return supabase.table("sales").insert(data).execute()
