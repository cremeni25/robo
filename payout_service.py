# payout_service.py
from supabase import Client
from decimal import Decimal
from datetime import datetime


def criar_payout(
    supabase: Client,
    *,
    partner_id: str,
    balance_id: str,
    amount: Decimal,
    provider: str,
    provider_account_id: str
):
    return (
        supabase
        .table("payouts")
        .insert({
            "partner_id": partner_id,
            "balance_id": balance_id,
            "amount": float(amount),
            "payout_provider": provider,
            "provider_account_id": provider_account_id,
            "payout_status": "pending"
        })
        .execute()
    )


def marcar_payout_como_pago(
    supabase: Client,
    *,
    payout_id: str,
    provider_reference: str
):
    payout = (
        supabase
        .table("payouts")
        .select("*")
        .eq("id", payout_id)
        .single()
        .execute()
        .data
    )

    # Atualiza payout
    supabase.table("payouts").update({
        "payout_status": "paid",
        "provider_reference": provider_reference,
        "processed_at": datetime.utcnow().isoformat()
    }).eq("id", payout_id).execute()

    # Atualiza saldo
    supabase.table("partner_balances").update({
        "available_balance": supabase.rpc(
            "subtract_balance", {"value": payout["amount"]}
        ),
        "paid_balance": supabase.rpc(
            "add_paid_balance", {"value": payout["amount"]}
        ),
        "updated_at": datetime.utcnow().isoformat()
    }).eq("id", payout["balance_id"]).execute()
