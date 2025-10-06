# create_view.py  — versão síncrona (Option 1)
import os
from sqlalchemy import create_engine, text

# URL principal (pode ser async na env); aqui derivamos a versão síncrona
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:admin@localhost:5432/techchallenge_db")
DATABASE_URL_SYNC = DATABASE_URL.replace("+asyncpg", "")  # vira postgresql://...

SQL_CREATE_VIEW = """
DROP VIEW IF EXISTS public.viticultura_view CASCADE;

CREATE VIEW public.viticultura_view AS
WITH anos AS (
    SELECT ano FROM public.producao
    UNION
    SELECT ano FROM public.processamento
    UNION
    SELECT ano FROM public.comercializacao
    UNION
    SELECT ano FROM public.importacao
    UNION
    SELECT ano FROM public.exportacao
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
    a.ano,
    COALESCE(prod.producao_total, 0)         AS producao_total,
    COALESCE(proc.processamento_total, 0)    AS processamento_total,
    COALESCE(com.comercializacao_total, 0)   AS comercializacao_total,
    COALESCE(imp.importacao_qtd, 0)          AS importacao_qtd,
    COALESCE(imp.importacao_valor, 0)        AS importacao_valor,
    COALESCE(exp.exportacao_qtd, 0)          AS exportacao_qtd,
    COALESCE(exp.exportacao_valor, 0)        AS exportacao_valor
FROM anos a
LEFT JOIN prod ON prod.ano = a.ano
LEFT JOIN proc ON proc.ano = a.ano
LEFT JOIN com  ON com.ano  = a.ano
LEFT JOIN imp  ON imp.ano  = a.ano
LEFT JOIN exp  ON exp.ano  = a.ano
ORDER BY a.ano;
"""

def create_view():
    engine = create_engine(DATABASE_URL_SYNC, future=True)
    with engine.begin() as conn:
        conn.execute(text(SQL_CREATE_VIEW))
    print("✅ View public.viticultura_view criada/atualizada com sucesso!")

if __name__ == "__main__":
    create_view()
