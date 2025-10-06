from typing import List, Optional, Dict

from fastapi import APIRouter, status, Depends, HTTPException, Response, Query

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.deps import get_session, get_current_user
from models.user_model import UserModel
from schemas.importacao_schema import ImportacaoSchema
from models.importacao_model import ImportacaoModel



router = APIRouter()


# GET Produtos
@router.get('/', response_model=List[ImportacaoSchema])
async def get_importacao(db: AsyncSession = Depends(get_session), current_user: UserModel = Depends(get_current_user)):
    async with db as session:
        query = select(ImportacaoModel)
        result = await session.execute(query)
        importacao: List[ImportacaoModel] = result.scalars().unique().all()

        return importacao



@router.get('/get_import_ano_min_max', response_model=List[ImportacaoSchema], status_code=status.HTTP_200_OK)
async def get_import_ano_min_max(
    ano_min: Optional[int] = None,
    ano_max: Optional[int] = None,
    db: AsyncSession = Depends(get_session),
        current_user: UserModel = Depends(get_current_user)
):
    async with db as session:
        query = select(ImportacaoModel)

        if ano_min is not None:
            query = query.where(ImportacaoModel.ano >= ano_min)
        if ano_max is not None:
            query = query.where(ImportacaoModel.ano <= ano_max)

        result = await session.execute(query)
        importacao = result.scalars().all()

        if importacao:
            return importacao
        else:
            raise HTTPException(status_code=404, detail="Nenhum dado encontrado no intervalo especificado.")




@router.get('/get_importacao_by_ano',response_model=List[ImportacaoSchema],status_code=status.HTTP_200_OK)
async def get_importacao_by_ano(
    ano: int = Query(1970),
    db: AsyncSession = Depends(get_session),
        current_user: UserModel = Depends(get_current_user)
):
    async with db as session:
        query = select(ImportacaoModel).where(ImportacaoModel.ano == ano)
        result = await session.execute(query)
        importacao = result.scalars().all()

        # Conversão para schema Pydantic
        return [ImportacaoSchema.model_validate(c) for c in importacao]
