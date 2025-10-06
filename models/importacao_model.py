from sqlalchemy import Column, Integer, String, Float, PrimaryKeyConstraint
from core.settings import DBBaseModel


class ImportacaoModel(DBBaseModel):
    __tablename__ = "importacao"

    pais_id = Column(Integer)  # pode variar com produto/ano
    pais = Column(String, nullable=False)
    ano = Column(Integer, nullable=False)
    produto = Column(String, nullable=False)
    quantidade = Column(Float)
    valor = Column(Float)

    __table_args__ = (
        PrimaryKeyConstraint("pais", "ano", "produto", name="pk_importacao_pais_ano_produto"),
    )
