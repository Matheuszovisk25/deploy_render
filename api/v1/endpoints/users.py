from typing import List, Optional

from fastapi import APIRouter, status, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user, get_session
from core.security import get_password_hash
from models.user_model import UserModel
from schemas.user_schema import UserOut, UserUpdate

router = APIRouter()

# ------- Quem está logado (precisa de JWT)
@router.get("/me", response_model=UserOut)
async def get_me(current_user: UserModel = Depends(get_current_user)):
    return current_user

# ------- Listar todos (protegido por JWT)
@router.get("/", response_model=List[UserOut])
async def get_users_all(db: AsyncSession = Depends(get_session),
                        current_user: UserModel = Depends(get_current_user)):
    result = await db.execute(select(UserModel))
    users = result.scalars().unique().all()
    return users  # Pydantic converte pelo from_attributes

# ------- Buscar por id (protegido)
@router.get("/by-id/{user_id}", response_model=UserOut, status_code=status.HTTP_200_OK)
async def get_user(user_id: int,
                   db: AsyncSession = Depends(get_session),
                   current_user: UserModel = Depends(get_current_user)):
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalars().unique().one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    return user

# ------- Atualizar (protegido)
@router.put("/{user_id}", response_model=UserOut, status_code=status.HTTP_202_ACCEPTED)
async def update_user(user_id: int,
                      payload: UserUpdate,
                      db: AsyncSession = Depends(get_session),
                      current_user: UserModel = Depends(get_current_user)):
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalars().unique().one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    # Atualiza campos se vierem
    if payload.name is not None:
        user.name = payload.name
    if payload.surname is not None:
        user.surname = payload.surname
    if payload.email is not None:
        user.email = payload.email.lower().strip()
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.password is not None and payload.password.strip():
        user.password = get_password_hash(payload.password)

    try:
        await db.commit()
        await db.refresh(user)
        return user
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="E-mail já está em uso.")

# ------- Deletar (protegido)
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int,
                      db: AsyncSession = Depends(get_session),
                      current_user: UserModel = Depends(get_current_user)):
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalars().unique().one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    await db.delete(user)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
