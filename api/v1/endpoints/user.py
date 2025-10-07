from typing import List

from fastapi import APIRouter, status, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from core.auth import authenticate_user, create_access_token
from core.deps import get_current_user, get_session
from core.security import get_password_hash
from models.user_model import UserModel
from schemas.user_schema import UserSchema, UserSchemaCreate, UserSchemaUp

router = APIRouter(prefix="/users", tags=["users"])


# ---------------------------
# WHOAMI (requer autenticado)
# ---------------------------
@router.get("/logado", response_model=UserSchema)
async def get_logado(current_user: UserModel = Depends(get_current_user)):
    # garante compat com response_model Pydantic v2
    return UserSchema.model_validate(current_user)


# ---------------------------
# SIGNUP (público)
# ---------------------------
@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=UserSchema)
async def post_create_user(
    user: UserSchemaCreate,
    db: AsyncSession = Depends(get_session),
):
    new_user = UserModel(
        name=user.name,
        surname=user.surname,
        email=user.email,
        password=get_password_hash(user.password),
    )
    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return UserSchema.model_validate(new_user)
    except IntegrityError:
        # e-mail duplicado (unique constraint)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Já existe usuário com este email cadastrado",
        )


# -------------------------------------------
# LISTAR USUÁRIOS (requer autenticado/admin?)
# -------------------------------------------
@router.get("/", response_model=List[UserSchema])
async def get_users_all(
    db: AsyncSession = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    result = await db.execute(select(UserModel))
    users = result.scalars().unique().all()
    return [UserSchema.model_validate(u) for u in users]


# -------------------------------------------
# OBTÉM USUÁRIO POR ID (requer autenticado)
# -------------------------------------------
@router.get("/by-id/{user_id}", response_model=UserSchema, status_code=status.HTTP_200_OK)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalars().unique().one_or_none()

    if user is None:
        raise HTTPException(
            detail="Usuário não encontrado.",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return UserSchema.model_validate(user)


# -------------------------------------------
# ATUALIZA USUÁRIO (requer autenticado)
# -------------------------------------------
@router.put("/{user_id}", response_model=UserSchema, status_code=status.HTTP_202_ACCEPTED)
async def update_user(
    user_id: int,
    user: UserSchemaUp,
    db: AsyncSession = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user_up = result.scalars().unique().one_or_none()

    if user_up is None:
        raise HTTPException(
            detail="Usuário não encontrado.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # Atualiza campos fornecidos
    if user.name is not None:
        user_up.name = user.name
    if user.surname is not None:
        user_up.surname = user.surname
    if user.email is not None:
        user_up.email = user.email
    if user.is_admin is not None:
        user_up.is_admin = user.is_admin
    if user.is_active is not None:
        user_up.is_active = user.is_active
    if user.password is not None:
        user_up.password = get_password_hash(user.password)

    await db.commit()
    await db.refresh(user_up)
    return UserSchema.model_validate(user_up)


# -------------------------------------------
# DELETA USUÁRIO (requer autenticado)
# -------------------------------------------
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def get_user_del(
    user_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user_del = result.scalars().unique().one_or_none()

    if user_del is None:
        raise HTTPException(
            detail="Usuário não encontrado.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    await db.delete(user_del)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------
# LOGIN (público)
# ---------------------------
@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session),
):
    user = await authenticate_user(
        email=form_data.username,
        password=form_data.password,
        db=db,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dados de acesso incorretos.",
        )

    token = create_access_token(sub=user.id)
    return JSONResponse(
        content={"access_token": token, "token_type": "bearer"},
        status_code=status.HTTP_200_OK,
    )
