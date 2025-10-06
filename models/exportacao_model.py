from sqlalchemy import Column, Integer, String, Float, PrimaryKeyConstraint
from core.settings import DBBaseModel

class ExportacaoModel(DBBaseModel):
    __tablename__ = "exportacao"

    pais_id = Column(Integer)  # pode variar com produto/ano
    pais = Column(String, nullable=False)
    ano = Column(Integer, nullable=False)
    produto = Column(String, nullable=False)
    quantidade = Column(Float)
    valor = Column(Float)

    __table_args__ = (
        PrimaryKeyConstraint("pais", "ano", "produto", name="pk_exportacao_pais_ano_produto"),
    )



