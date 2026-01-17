# balance_service.py
from supabase import Client
from decimal import Decimal
from datetime import datetime


def garantir_balance(supabase: Client, partner_id: str):
    res = (
        supabase
        .table("partner_balances")
        .select("*")
        .eq("partner_id", partner_id)
        .single()
        .execute()
    )

    if res.data:
        return res.data

    return (
        supabase
        .table("partner_balances")
        .insert({"partner_id": partner_id})
        .execute()
        .data[0]
    )


def adicionar_comissao(
    supabase: Client,
    *,
    partner_id: str,
    valor: Decimal
):
    balance = garantir_balance(supabase, partner_id)

    novo_total = Decimal(balance["total_generated"]) + valor
    novo_disponivel = Decimal(balance["available_balance"]) + valor

    return (
        supabase
        .table("partner_balances")
        .update({
            "total_generated": float(novo_total),
            "available_balance": float(novo_disponivel),
            "updated_at": datetime.utcnow().isoformat()
        })
        .eq("partner_id", partner_id)
        .execute()
    )
