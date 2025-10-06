from pydantic import BaseModel
from typing import Optional

class ExportacaoSchema(BaseModel):
    pais_id: Optional[int] = None
    pais: str
    ano: int
    produto: str
    quantidade: Optional[float] = None
    valor: Optional[float] = None

    model_config = {
        "from_attributes": True
    }

class ExportacaoSchemaCreate(ExportacaoSchema):
    pais_id: Optional[int] = None
    pais: str
    ano: int
    produto: str
    quantidade: Optional[float] = None
    valor: Optional[float] = None


class ExportacaoSchemaUpdate(BaseModel):
    quantidade: Optional[float] = None
    valor: Optional[float] = None

    model_config = {
        "from_attributes": True
    }
