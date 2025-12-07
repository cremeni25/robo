@app.get("/ranking")
def ranking():
    try:
        query = """
            SELECT
                p.id_produto,
                p.nome,
                COALESCE(SUM(m.valor), 0) AS pontuacao_total
            FROM produtos p
            LEFT JOIN metrica_historico m
                ON m.id_produto = p.id_produto
            GROUP BY p.id_produto, p.nome
            ORDER BY pontuacao_total DESC;
        """

        result = supabase.rpc("executar_query", {"query": query}).execute()

        dados = result.data

        # Ajuste para qualquer formato retornado
        if isinstance(dados, list):
            return dados

        if isinstance(dados, dict):
            return [dados]

        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
