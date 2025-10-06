from typing import List

from fastapi import APIRouter, status, Depends, HTTPException, Response
# ❌ REMOVA esta linha: from fastapi.openapi.models import Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from core.auth import authenticate_user, create_access_token
from models.user_model import UserModel
from schemas.user_schema import UserSchema, UserSchemaCreate, UserSchemaUp
from core.deps import get_current_user, get_session
from core.security import get_password_hash

router = APIRouter()

# GET LOGADO
@router.get("/logado", response_model=UserSchema)
def get_logado(current_user: UserModel = Depends(get_current_user)):
    return current_user

# SIGNUP
@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=UserSchema)
async def post_create_user(user: UserSchemaCreate, db: AsyncSession = Depends(get_session)):
    new_user = UserModel(
        name=user.name,
        surname=user.surname,
        email=user.email.lower(),                 # normaliza
        password=get_password_hash(user.password) # hash
    )
    async with db as session:
        try:
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)       # garante id/população
            return UserSchema.model_validate(new_user)
        except IntegrityError:
            await session.rollback()              # ✅ rollback para limpar a transação
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,   # ou 409
                detail="Já existe usuário com este email cadastrado"
            )

# LIST USERS
@router.get("/", response_model=List[UserSchema])
async def get_users_all(session: AsyncSession = Depends(get_session),
                        current_user: UserModel = Depends(get_current_user)):
    result = await session.execute(select(UserModel))
    users = result.unique().scalars().all()
    return [UserSchema.model_validate(u) for u in users]

# GET USER BY ID
@router.get('/by-id/{user_id}', response_model=UserSchema, status_code=status.HTTP_200_OK)
async def get_user(user_id: int,
                   db: AsyncSession = Depends(get_session),
                   current_user: UserModel = Depends(get_current_user)):
    async with db as session:
        result = await session.execute(select(UserModel).filter(UserModel.id == user_id))
        user = result.scalars().unique().one_or_none()
        if user:
            return UserSchema.model_validate(user)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Usuário não encontrado.')

# UPDATE
@router.put('/{user_id}', response_model=UserSchema, status_code=status.HTTP_202_ACCEPTED)
async def update_user(user_id: int,
                      user: UserSchemaUp,
                      db: AsyncSession = Depends(get_session),
                      current_user: UserModel = Depends(get_current_user)):
    async with db as session:
        result = await session.execute(select(UserModel).filter(UserModel.id == user_id))
        user_up = result.scalars().unique().one_or_none()
        if not user_up:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Usuário não encontrado.')

        if user.name is not None: user_up.name = user.name
        if user.surname is not None: user_up.surname = user.surname
        if user.email is not None: user_up.email = user.email.lower()
        if getattr(user, "is_admin", None) is not None: user_up.is_admin = user.is_admin
        if getattr(user, "is_active", None) is not None: user_up.is_active = user.is_active
        if user.password is not None: user_up.password = get_password_hash(user.password)

        await session.commit()
        await session.refresh(user_up)
        return UserSchema.model_validate(user_up)

# DELETE
@router.delete('/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def get_user_del(user_id: int,
                       db: AsyncSession = Depends(get_session),
                       current_user: UserModel = Depends(get_current_user)):
    async with db as session:
        result = await session.execute(select(UserModel).where(UserModel.id == user_id))
        user_del = result.scalars().unique().one_or_none()
        if not user_del:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Usuário não encontrado.')

        await session.delete(user_del)
        await session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

# LOGIN (form-encoded)
@router.post('/login')
async def login(form_data: OAuth2PasswordRequestForm = Depends(),
                db: AsyncSession = Depends(get_session)):
    user = await authenticate_user(email=form_data.username, password=form_data.password, db=db)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Dados de acesso incorretos.')
    return JSONResponse(
        content={"access_token": create_access_token(sub=user.id), "token_type": "bearer"},
        status_code=status.HTTP_200_OK
    )
