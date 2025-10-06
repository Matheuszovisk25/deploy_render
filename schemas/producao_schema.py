from typing import Optional
from pydantic import BaseModel


class ProducaoSchema(BaseModel):
    produto_id: int
    produto_tipo: str
    produto_nome: str
    ano: int
    quantidade: Optional[float] = None

    model_config = {
        "from_attributes": True
    }


class ProducaoSchemaList(BaseModel):
    produto_id: int
    produto_tipo: str
    produto_nome: str

    model_config = {
        "from_attributes": True
    }


class ProducaoSchemaSchemaUp(BaseModel):
    quantidade: Optional[float] = None

    model_config = {
        "from_attributes": True
    }
