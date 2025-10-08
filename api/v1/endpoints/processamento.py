from typing import List, Optional, Dict

from fastapi import APIRouter, status, Depends, HTTPException, Response, Query

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.deps import get_session, get_current_user
from models.user_model import UserModel
from schemas.processamento_schema import ProcessamentoSchema
from models.processamento_model import ProcessamentoModel



router = APIRouter()


# GET Produtos
@router.get('/', response_model=List[ProcessamentoSchema])
async def get_processamento(db: AsyncSession = Depends(get_session), current_user: UserModel = Depends(get_current_user)):
    async with db as session:
        query = select(ProcessamentoModel)
        result = await session.execute(query)
        processamento: List[ProcessamentoModel] = result.scalars().unique().all()

        return processamento

@router.get('/get_processamento_ano_min_max', response_model=List[ProcessamentoSchema], status_code=status.HTTP_200_OK)
async def get_processamento_ano_min_max(
        ano_min: Optional[int] = None,
            ano_max: Optional[int] = None,
            db: AsyncSession = Depends(get_session),
            current_user: UserModel = Depends(get_current_user)

    ):
        async with db as session:
            query = select(ProcessamentoModel)

            if ano_min is not None:
                query = query.where(ProcessamentoModel.ano >= ano_min)
            if ano_max is not None:
                query = query.where(ProcessamentoModel.ano <= ano_max)

            result = await session.execute(query)
            processamento = result.scalars().all()

            if processamento:
                return processamento
            else:
                raise HTTPException(status_code=404, detail="Nenhum dado encontrado no intervalo especificado.")




@router.get('/get_processamento_by_ano',response_model=List[ProcessamentoSchema],status_code=status.HTTP_200_OK)
async def get_processamento_by_ano(
    ano: int = Query(1970),
    db: AsyncSession = Depends(get_session),
        current_user: UserModel = Depends(get_current_user)
):
    async with db as session:
        query = select(ProcessamentoModel).where(ProcessamentoModel.ano == ano)
        result = await session.execute(query)
        processamento = result.scalars().all()

        # Conversão para schema Pydantic
        return [ProcessamentoSchema.model_validate(c) for c in processamento]
