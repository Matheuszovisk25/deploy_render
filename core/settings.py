from pydantic_settings import BaseSettings
from sqlalchemy.orm import declarative_base

DBBaseModel = declarative_base()

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    #DB_URL: str = "postgresql+asyncpg://postgres:admin@localhost:5432/techchallenge_db"
    DB_URL: str = "postgresql+asyncpg://admin_fkij_user:A8ygffEUSBFsWCmdnvAB4i6xw0PdDt69@dpg-d3i2c60gjchc73asutpg-a:5432/admin_fkij?ssl=require"
    JWT_SECRET_KEY: str = '75d13f95c062c9ab0f1a59ea5959df76'
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 semana

    class Config:
        case_sensitive = True

settings = Settings()


#import secrets
#token: str = secrets.token_urlsafe(32)
