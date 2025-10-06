import os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine
from core.settings import settings
from core.database import engine

# Criar engine síncrono a partir do URL async
sync_engine = create_engine(settings.DB_URL.replace("+asyncpg", ""))

def carregar_dados(caminho_csv: Path, produto_nome: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(caminho_csv, sep="\t", encoding="utf-8-sig")
        if df.shape[1] == 1:
            df = pd.read_csv(caminho_csv, sep=";", encoding="latin1")
    except Exception as e:
        print(f"❌ Erro ao ler {caminho_csv.name}: {e}")
        return pd.DataFrame()

    df.columns = df.columns.str.strip()

    if len(df.columns) < 2:
        print(f"⚠️ Arquivo {caminho_csv.name} não possui colunas suficientes.")
        return pd.DataFrame()

    df.rename(columns={
        df.columns[0]: "pais_id",
        df.columns[1]: "pais"
    }, inplace=True)

    df = df.drop(columns=["ano", "valor"], errors="ignore")

    col_ano = [col for col in df.columns if col[:4].isdigit()]
    if not col_ano:
        print(f"⚠️ Nenhuma coluna de ano encontrada em {caminho_csv.name}.")
        return pd.DataFrame()

    # Verifica se os anos estão duplicados (quantidade + valor)
    anos_unicos = list(dict.fromkeys([col[:4] for col in col_ano]))
    if len(anos_unicos) * 2 == len(col_ano):
        col_quantidade = col_ano[::2]
        col_valor = col_ano[1::2]

        df_qtd = df.melt(
            id_vars=["pais_id", "pais"],
            value_vars=col_quantidade,
            var_name="ano",
            value_name="quantidade"
        )

        df_val = df.melt(
            id_vars=["pais_id", "pais"],
            value_vars=col_valor,
            var_name="ano",
            value_name="valor"
        )

        df_qtd["ano"] = df_qtd["ano"].str.extract(r"(\d{4})")
        df_val["ano"] = df_val["ano"].str.extract(r"(\d{4})")

        df_meltado = df_qtd.merge(df_val, on=["pais_id", "pais", "ano"])
    else:
        df_meltado = df.melt(
            id_vars=["pais_id", "pais"],
            value_vars=col_ano,
            var_name="ano",
            value_name="valor"
        )
        df_meltado["ano"] = df_meltado["ano"].str.extract(r"(\d{4})")

    df_meltado["valor"] = (
        df_meltado["valor"]
        .astype(str)
        .replace(["*", "nd"], pd.NA)
        .str.replace(",", ".", regex=False)
    )
    df_meltado["valor"] = pd.to_numeric(df_meltado["valor"], errors="coerce")

    if "quantidade" in df_meltado.columns:
        df_meltado["quantidade"] = (
            df_meltado["quantidade"]
            .astype(str)
            .replace(["*", "nd"], pd.NA)
            .str.replace(",", ".", regex=False)
        )
        df_meltado["quantidade"] = pd.to_numeric(df_meltado["quantidade"], errors="coerce")

    df_meltado["produto"] = produto_nome.strip()

    print(f"✔️ Produto atribuído: {produto_nome} → {df_meltado['produto'].unique()}")

    return df_meltado

def salvar_no_banco(df: pd.DataFrame):
    try:
        df.drop_duplicates(subset=["pais", "ano", "produto"], inplace=True)
        df.to_sql("importacao", con=sync_engine, if_exists="append", index=False)
        print("✅ Dados inseridos no banco com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao salvar no banco: {e}")

def limpar_dataframe():
    BASE_DIR = Path("./data_process/data_scraping/importacao")

    TIPOS_PRODUTO = {
        "Espumantes": "espumante",
        "Uvas frescas": "uvas frescas",
        "Uvas passas": "uvas passas",
        "Suco de uva": "suco de uva",
        "Vinhos de mesa": "vinhos de mesa"
    }

    ARQUIVOS_CSV = {
        "Espumantes": "ImpEspumantes.csv",
        "Uvas frescas": "ImpFrescas.csv",
        "Uvas passas": "ImpPassas.csv",
        "Suco de uva": "ImpSuco.csv",
        "Vinhos de mesa": "ImpVinhos.csv"
    }

    dataframes = []

    for pasta_nome, produto_nome in TIPOS_PRODUTO.items():
        nome_arquivo = ARQUIVOS_CSV[pasta_nome]
        caminho_arquivo = BASE_DIR / pasta_nome / nome_arquivo
        print(f"🧭 Caminho absoluto: {caminho_arquivo.resolve()}")
        if caminho_arquivo.exists():
            print(f"📥 Lendo: {caminho_arquivo}")
            df_tipo = carregar_dados(caminho_arquivo, produto_nome)
            if not df_tipo.empty:
                print(f"📊 Produto contido: {df_tipo['produto'].unique()}")
                dataframes.append(df_tipo)
            else:
                print(f"⚠️ Dados vazios após limpeza: {caminho_arquivo.name}")
        else:
            print(f"🚫 Arquivo não encontrado: {caminho_arquivo}")

    if not dataframes:
        print("❌ Nenhum dado foi processado.")
        return

    df_final = pd.concat(dataframes, ignore_index=True)
    df_final.reset_index(drop=True, inplace=True)

    print("🔎 Amostra agrupada por produto:")
    print(df_final.groupby("produto").size())

    print(f"✅ Dados combinados com sucesso: {df_final.shape[0]} linhas, {df_final.shape[1]} colunas")

    df_final.to_csv("./data_process/data_scraping/importacao/dados_importacao_unificada.csv", index=False)
    print("💾 Arquivo salvo como 'dados_importacao_unificada.csv'")

    salvar_no_banco(df_final)



