from sqlalchemy import Column, Integer, String, Float, PrimaryKeyConstraint
from core.settings import DBBaseModel

class ProcessamentoModel(DBBaseModel):
    __tablename__ = "processamento"

    produto_id = Column(Integer, nullable=False)
    produto_tipo = Column(String, nullable=False)
    produto_nome = Column(String, nullable=False)
    ano = Column(Integer, nullable=False)
    quantidade = Column(Float, nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint("produto_id", "ano", name="pk_produto_processamento_ano"),
    )