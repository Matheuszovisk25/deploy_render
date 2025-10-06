from pytz import timezone
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt
from models.user_model import UserModel
from core.settings import settings
from core.security import verify_password
from pydantic import EmailStr

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/users/login")

async def authenticate_user(db: AsyncSession, email: EmailStr, password: str) -> Optional[UserModel]:
    async with db as session:
        query = select(UserModel).filter(UserModel.email == email)
        result = await session.execute(query)
        #user:UserModel = result.scalar().unique.one_or_none()
        user: UserModel = result.scalars().unique().one_or_none()
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        return user


def create_token(toke_type: str, time_expire: timedelta, sub:str) -> str:
    #https://datetracjer.ietf.org/html...
    payload = {}
    sp = timezone('America/Sao_Paulo')
    expire = datetime.now() + time_expire
    payload['exp'] = expire
    payload['sub'] = str(sub)
    payload['iat'] = datetime.now(sp)
    payload['type'] = toke_type


    #return jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(sub:str) -> str:
    #https://jwt.io
    return create_token("access_token", time_expire=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES), sub=sub)