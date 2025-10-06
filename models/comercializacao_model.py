from sqlalchemy import Column, Integer, String, BigInteger, PrimaryKeyConstraint, Float

from core.settings import DBBaseModel


class ComercializacaooModel(DBBaseModel):
    __tablename__ = "comercializacao"

    produto_id = Column(Integer, nullable=False)
    produto_tipo = Column(String, nullable=False)
    produto_nome = Column(String, nullable=False)
    ano = Column(Integer, nullable=False)
    quantidade = Column(Float, nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint("produto_id", "ano", name="pk_produto_comercializacao_ano"),
    )
