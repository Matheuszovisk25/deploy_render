from pydantic import BaseModel
from typing import Optional

class ImportacaoSchema(BaseModel):
    pais_id: Optional[int] = None
    pais: str
    ano: int
    produto: str
    quantidade: Optional[float] = None
    valor: Optional[float] = None

    model_config = {
        "from_attributes": True
    }

class ImportacaoSchemaCreate(BaseModel):
    pais_id: Optional[int] = None
    pais: str
    ano: int
    produto: str
    quantidade: Optional[float] = None
    valor: Optional[float] = None



class ImportacaoSchemaUpdate(BaseModel):
    quantidade: Optional[float] = None
    valor: Optional[float] = None

    model_config = {
        "from_attributes": True
    }
