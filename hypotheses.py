# hypotheses.py — Fase 1.4 Hipótese Inicial Controlada
# Robô Global AI
# Arquivo VITAL — substituição total permitida

from datetime import datetime
from typing import List, Dict

# Catálogo base de padrões globais reais
# (não são execuções, não são dados financeiros)
GLOBAL_HYPOTHESIS_PATTERNS = [
    {
        "nicho": "educação_conhecimento",
        "canal": "organico",
        "acao": "captacao",
        "risco": "baixo",
        "motivo": "Demanda global recorrente e baixo custo de aquisição inicial"
    },
    {
        "nicho": "fitness_bem_estar",
        "canal": "organico",
        "acao": "captacao",
        "risco": "baixo",
        "motivo": "Alto interesse emocional e consumo contínuo"
    },
    {
        "nicho": "produtividade_renda",
        "canal": "organico",
        "acao": "captacao",
        "risco": "medio",
        "motivo": "Busca constante por melhoria financeira e performance"
    }
]

def gerar_hipoteses() -> List[Dict]:
    """
    Gera hipóteses iniciais controladas.
    NÃO executa ações externas.
    NÃO gera dados fictícios financeiros.
    """
    hipoteses = []
    now = datetime.utcnow().isoformat()

    for idx, base in enumerate(GLOBAL_HYPOTHESIS_PATTERNS, start=1):
        hipoteses.append({
            "id": f"HIP-{idx:03d}",
            "tipo": "HIPOTESE",
            "fase": "1.4",
            "status": "AGUARDANDO_APROVACAO",
            "nicho": base["nicho"],
            "canal": base["canal"],
            "acao": base["acao"],
            "risco": base["risco"],
            "motivo": base["motivo"],
            "criado_em": now
        })

    return hipoteses
