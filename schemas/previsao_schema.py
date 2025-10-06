# schemas/previsao_schema.py
from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, Field

class ForecastSeriesSchema(BaseModel):
    serie_id: str
    label: str
    produto: Optional[str] = None
    pais: Optional[str] = None

class PrevisaoSchema(BaseModel):
    id: int
    serie_id: str
    produto: Optional[str] = None
    pais: Optional[str] = None
    data: date
    ano: Optional[int] = None
    mes: Optional[int] = None
    y: Optional[float] = None
    yhat: float
    yhat_lower: Optional[float] = None
    yhat_upper: Optional[float] = None
    modelo: Optional[str] = None
    gerado_em: Optional[datetime] = Field(default=None)
