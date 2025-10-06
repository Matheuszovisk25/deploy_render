# load_all.py
import pandas as pd
from models.producao_model import ProducaoModel
from models.processamento_model import ProcessamentoModel
from models.comercializacao_model import ComercializacaoModel
from models.importacao_model import ImportacaoModel
from models.exportacao_model import ExportacaoModel

# Modifique este caminho para onde estão os seus CSVs
CAMINHO_CSV = "./data_process/data_scraping"

def load_producao_data(session):
    df = pd.read_csv(f"{CSV_DIR}/producao/Producao.csv")
    for _, row in df.iterrows():
        model = ProducaoModel(
            ano=row["ano"],
            produto=row["produto"],
            quantidade=row["quantidade"],
            valor=row["valor"],
        )
        session.add(model)
    session.commit()

def load_processamento_data(session):
    df = pd.read_csv(f"{CSV_DIR}/processamento/Processamento.csv")
    for _, row in df.iterrows():
        model = ProcessamentoModel(
            ano=row["ano"],
            produto=row["produto"],
            quantidade=row["quantidade"],
            valor=row["valor"],
        )
        session.add(model)
    session.commit()

def load_comercializacao_data(session):
    df = pd.read_csv(f"{CSV_DIR}/comercializacao/Comercializacao.csv")
    for _, row in df.iterrows():
        model = ComercializacaoModel(
            ano=row["ano"],
            produto=row["produto"],
            quantidade=row["quantidade"],
            valor=row["valor"],
        )
        session.add(model)
    session.commit()

def load_importacao_data(session):
    df = pd.read_csv(f"{CSV_DIR}/importacao/Importacao.csv")
    for _, row in df.iterrows():
        model = ImportacaoModel(
            ano=row["ano"],
            produto=row["produto"],
            quantidade=row["quantidade"],
            valor=row["valor"],
        )
        session.add(model)
    session.commit()

def load_exportacao_data(session):
    df = pd.read_csv(f"{CSV_DIR}/exportacao/Exportacao.csv")
    for _, row in df.iterrows():
        model = ExportacaoModel(
            ano=row["ano"],
            produto=row["produto"],
            quantidade=row["quantidade"],
            valor=row["valor"],
        )
        session.add(model)
    session.commit()

def main(session):
    load_producao_data(session)
    load_processamento_data(session)
    load_comercializacao_data(session)
    load_importacao_data(session)
    load_exportacao_data(session)

