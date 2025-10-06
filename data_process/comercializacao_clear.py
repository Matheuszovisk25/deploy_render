import os

from pandas.core.computation.ops import isnumeric
from sqlalchemy.dialects.mssql.information_schema import columns

from core.database import engine
import pandas as pd
from sqlalchemy import create_engine
from core.settings import settings

# Criar engine síncrono a partir do URL async
sync_engine = create_engine(settings.DB_URL.replace("+asyncpg", ""))


def limpar_data_frame(path_csv:str):
    try:
        df = pd.read_csv(path_csv, sep=";", encoding="utf-8")
        #Busca as colunas de ano no dataframe
        colunas_ano = [col for col in df.columns if  col.isnumeric()]
        df_data_melt = df.melt(
            id_vars=["id", "control", "Produto"],
            value_vars=colunas_ano,
            var_name="ano",
            value_name="quantidade"
        )
        #Renomeando os campos da tabela
        df_data_melt.rename(columns={
            'id':'produto_id',
            'control':'produto_tipo',
            'Produto':'produto_nome'
        }, inplace=True)

        # Limpeza do campo e preenchimento dos dados nulos
        df_data_melt["produto_tipo"] = (
            df_data_melt["produto_tipo"]
            .fillna("DESCONHECIDO")
            .astype(str)
            .str.strip()
        )

        df_data_melt["produto_nome"] = (
            df_data_melt["produto_nome"]
            .fillna("DESCONHECIDO")
            .astype(str)
            .str.strip()
        )

        #Limpando os dados do campo quantidade
        df_data_melt["quantidade"] = (
            df_data_melt["quantidade"]
            .astype(str).replace(["*", "nd"], pd.NA)
            .str.replace(",", ".", regex=False)
        )

        #convertendo os dados em numerico
        df_data_melt["quantidade"] = pd.to_numeric(df_data_melt["quantidade"], errors="coerce")

        #Busca e remove chaves duplicadas, cajo hajam na tabela
        df_data_melt.drop_duplicates(subset=["produto_id", "ano"], inplace=True)

        return df_data_melt

    except Exception as error:
        print(f"❌ Erro ao processar CSV: {error}")
        return pd.DataFrame()

#Salvando os dados no banco
def salvar_no_banco(df:pd.DataFrame):
    try:
        df.to_sql('comercializacao', con=sync_engine, if_exists='append', index=False)
        print(f"✅ Dados inseridos no banco com sucesso.")
    except Exception as error:
        print(f"❌ Erro ao salvar no banco: {error}")


