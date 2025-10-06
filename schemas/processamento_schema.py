from typing import Optional
from pydantic import BaseModel


class ProcessamentoSchema(BaseModel):
    produto_id: int
    produto_tipo: str
    produto_nome: str
    ano: int
    quantidade: Optional[float] = None

    model_config = {
        "from_attributes": True
    }


class ProcessamentoSchemaCreate(BaseModel):
    produto_id: int
    produto_tipo: str
    produto_nome: str
    ano: int
    quantidade: Optional[float] = None

    model_config = {
        "from_attributes": True
    }


class ProcessamentoSchemaUp(BaseModel):
    quantidade: Optional[float] = None

    model_config = {
        "from_attributes": True
    }
