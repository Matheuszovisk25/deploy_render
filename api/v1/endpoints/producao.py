from typing import List, Optional, Annotated, Dict

from fastapi import APIRouter, status, Depends, HTTPException, Response, Query

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.auth import authenticate_user, create_access_token
from models.producao_model import ProducaoModel
from models.user_model import UserModel
from schemas.producao_schema import ProducaoSchema, ProducaoSchemaList
from core.deps import get_current_user, get_session



router = APIRouter()


# GET Produtos
@router.get('/', response_model=List[ProducaoSchema])
async def get_producao(db: AsyncSession = Depends(get_session), current_user: UserModel = Depends(get_current_user)):
    async with db as session:
        query = select(ProducaoModel)
        result = await session.execute(query)
        producao: List[ProducaoModel] = result.scalars().unique().all()

        return producao



@router.get('/get_prod_ano_min_max', response_model=List[ProducaoSchema], status_code=status.HTTP_200_OK)
async def get_prod_ano_min_max(
    ano_min: Optional[int] = None,
    ano_max: Optional[int] = None,
    db: AsyncSession = Depends(get_session),
    current_user: UserModel = Depends(get_current_user)
):
    async with db as session:
        query = select(ProducaoModel)

        if ano_min is not None:
            query = query.where(ProducaoModel.ano >= ano_min)
        if ano_max is not None:
            query = query.where(ProducaoModel.ano <= ano_max)

        result = await session.execute(query)
        producoes = result.scalars().all()

        if producoes:
            return producoes
        else:
            raise HTTPException(status_code=404, detail="Nenhum dado encontrado no intervalo especificado.")



@router.get('/get_producao_by_ano',response_model=List[ProducaoSchema],status_code=status.HTTP_200_OK)
async def get_producao_by_ano(
    ano: int = Query(1970),
    db: AsyncSession = Depends(get_session),
        current_user: UserModel = Depends(get_current_user)
):
    async with db as session:
        query = select(ProducaoModel).where(ProducaoModel.ano == ano)
        result = await session.execute(query)
        producao = result.scalars().all()

        # Conversão para schema Pydantic
        return [ProducaoSchema.model_validate(c) for c in producao]
