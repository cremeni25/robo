# commission_service.py
from decimal import Decimal


def calcular_comissao(
    *,
    commission_total: Decimal,
    percentual_parceiro: Decimal
):
    """
    percentual_parceiro: ex 0.6 = 60%
    """
    partner_commission = commission_total * percentual_parceiro
    master_commission = commission_total - partner_commission

    return {
        "partner_commission": partner_commission,
        "master_commission": master_commission
    }
