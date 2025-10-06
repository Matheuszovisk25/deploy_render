from typing import List, Optional, Dict

from fastapi import APIRouter, status, Depends, HTTPException, Response, Query

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.deps import get_session, get_current_user
from models.user_model import UserModel
from schemas.exportacao_schema import ExportacaoSchema
from models.exportacao_model import ExportacaoModel



router = APIRouter()


# GET Produtos
@router.get('/', response_model=List[ExportacaoSchema])
async def get_exportacao(db: AsyncSession = Depends(get_session), current_user: UserModel = Depends(get_current_user)):
    async with db as session:
        query = select(ExportacaoModel)
        result = await session.execute(query)
        exportacao = result.scalars().unique().all()

        return [ExportacaoSchema.model_validate(item) for item in exportacao]



@router.get('/get_export_ano_min_max', response_model=List[ExportacaoSchema], status_code=status.HTTP_200_OK)
async def get_export_ano_min_max(
        ano_min: Optional[int] = None,
        ano_max: Optional[int] = None,
        db: AsyncSession = Depends(get_session),
        current_user: UserModel = Depends(get_current_user)

):
    async with db as session:
        query = select(ExportacaoModel)

        if ano_min is not None:
            query = query.where(ExportacaoModel.ano >= ano_min)
        if ano_max is not None:
            query = query.where(ExportacaoModel.ano <= ano_max)

        result = await session.execute(query)
        exportacao = result.scalars().all()

        if exportacao:
            return exportacao
        else:
            raise HTTPException(status_code=404, detail="Nenhum dado encontrado no intervalo especificado.")





@router.get('/get_exportacao_by_ano',response_model=List[ExportacaoSchema],status_code=status.HTTP_200_OK)
async def get_exportacao_by_ano(
    ano: int = Query(1970),
    db: AsyncSession = Depends(get_session),
    current_user: UserModel = Depends(get_current_user)

):
    async with db as session:
        query = select(ExportacaoModel).where(ExportacaoModel.ano == ano)
        result = await session.execute(query)
        exportacao = result.scalars().all()

        # Conversão para schema Pydantic
        return [ExportacaoSchema.model_validate(c) for c in exportacao]