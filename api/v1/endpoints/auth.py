from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import JSONResponse

from core.deps import get_session
from core.security import get_password_hash
from core.auth import authenticate_user, create_access_token
from models.user_model import UserModel
from schemas.user_schema import UserCreate, UserOut

router = APIRouter()
@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserOut)
async def register_user(payload: UserCreate, db: AsyncSession = Depends(get_session)):
    email = payload.email.lower().strip()

    # checagem prévia pra resposta mais rápida
    exists = await db.execute(select(UserModel.id).where(UserModel.email == email))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Já existe usuário com este email cadastrado.")

    user = UserModel(
        name=payload.name,
        surname=payload.surname,
        email=email,
        password=get_password_hash(payload.password),  # hash
        # is_admin False / is_active True via defaults no model
    )
    try:
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user  # filtrado por UserOut
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Já existe usuário com este email cadastrado.")

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(),
                db: AsyncSession = Depends(get_session)):
    user = await authenticate_user(email=form_data.username, password=form_data.password, db=db)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Dados de acesso incorretos.")
    return JSONResponse(
        content={"access_token": create_access_token(sub=user.id), "token_type": "bearer"},
        status_code=status.HTTP_200_OK
    )
