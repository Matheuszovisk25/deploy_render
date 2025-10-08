# api/v1/sintese.py
from __future__ import annotations
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

router = APIRouter()

# ---- pegue o provedor de sessão async do seu projeto ----
# Tente importar de onde você já usa nos outros endpoints:
try:
    from core.database import get_session  # ajuste se seu projeto usar outro caminho
except Exception:
    # fallback opcional: se o caminho acima não existir, altere para o correto
    raise

SQL_SINTESE = text("""
WITH anos AS (
    SELECT DISTINCT ano FROM public.producao
    UNION
    SELECT DISTINCT ano FROM public.processamento
    UNION
    SELECT DISTINCT ano FROM public.comercializacao
    UNION
    SELECT DISTINCT ano FROM public.importacao
    UNION
    SELECT DISTINCT ano FROM public.exportacao
),
prod AS (
    SELECT ano, SUM(quantidade) AS producao_total
    FROM public.producao
    GROUP BY ano
),
proc AS (
    SELECT ano, SUM(quantidade) AS processamento_total
    FROM public.processamento
    GROUP BY ano
),
com AS (
    SELECT ano, SUM(quantidade) AS comercializacao_total
    FROM public.comercializacao
    GROUP BY ano
),
imp AS (
    SELECT ano,
           SUM(quantidade) AS importacao_qtd,
           COALESCE(SUM(valor),0) AS importacao_valor
    FROM public.importacao
    GROUP BY ano
),
exp AS (
    SELECT ano,
           SUM(quantidade) AS exportacao_qtd,
           COALESCE(SUM(valor),0) AS exportacao_valor
    FROM public.exportacao
    GROUP BY ano
)
SELECT
    a.ano::int                                           AS ano,
    COALESCE(prod.producao_total, 0)::numeric            AS producao_total,
    COALESCE(proc.processamento_total, 0)::numeric       AS processamento_total,
    COALESCE(com.comercializacao_total, 0)::numeric      AS comercializacao_total,
    COALESCE(imp.importacao_qtd, 0)::numeric             AS importacao_qtd,
    COALESCE(imp.importacao_valor, 0)::numeric           AS importacao_valor,
    COALESCE(exp.exportacao_qtd, 0)::numeric             AS exportacao_qtd,
    COALESCE(exp.exportacao_valor, 0)::numeric           AS exportacao_valor
FROM anos a
LEFT JOIN prod ON prod.ano = a.ano
LEFT JOIN proc ON proc.ano = a.ano
LEFT JOIN com  ON com.ano  = a.ano
LEFT JOIN imp  ON imp.ano  = a.ano
LEFT JOIN exp  ON exp.ano  = a.ano
ORDER BY a.ano;
""")

@router.get("/", summary="Síntese anual (equivalente à VIEW)")
async def get_sintese(
    ano_min: Optional[int] = Query(None, ge=0),
    ano_max: Optional[int] = Query(None, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """
    Retorna uma linha por ano com totais:
    producao_total, processamento_total, comercializacao_total,
    importacao_qtd, importacao_valor, exportacao_qtd, exportacao_valor.
    Filtros opcionais: ano_min, ano_max.
    """
    result = await session.execute(SQL_SINTESE)
    rows = result.mappings().all()
    if not rows:
        return []

    # aplica filtros em memória (simples e eficiente para poucos anos)
    out = []
    for r in rows:
        y = int(r["ano"])
        if ano_min is not None and y < ano_min:
            continue
        if ano_max is not None and y > ano_max:
            continue
        out.append({k: (float(v) if isinstance(v, (int, float)) else v) for k, v in dict(r).items()})

    return out
