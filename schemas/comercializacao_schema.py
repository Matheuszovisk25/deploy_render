from typing import Optional
from pydantic import BaseModel


class ComercializacaoSchema(BaseModel):
    produto_id: int
    produto_tipo: str
    produto_nome: str
    ano: int
    quantidade: Optional[float] = None

    model_config = {
        "from_attributes": True
    }


class ComercializacaoSchemaCreate(BaseModel):
    produto_id: int
    produto_tipo: str
    produto_nome: str
    ano: int
    quantidade: Optional[float] = None

    model_config = {
        "from_attributes": True
    }


class ComercializacaoSchemaSchemaUp(BaseModel):
    quantidade: Optional[float] = None

    model_config = {
        "from_attributes": True
    }
