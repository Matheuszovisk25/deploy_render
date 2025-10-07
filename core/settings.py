from pydantic_settings import BaseSettings
from sqlalchemy.orm import declarative_base

DBBaseModel = declarative_base()

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    #DB_URL: str = "postgresql+asyncpg://admin:mTeHvN2zSYQWgmqlNsCOuSoxKqtYzAGL@dpg-d0ua86idbo4c73ap46q0-a/db_techchalenge"
    DB_URL: str = "postgresql+asyncpg://db_techchalenge:zKTL1lbgJPJqrow4lwCRPDDtzKcAumn9@dpg-d3i5ffs9c44c73agfiqg-a.oregon-postgres.render.com/db_techchalenge_fef9"
    JWT_SECRET_KEY: str = '75d13f95c062c9ab0f1a59ea5959df76'
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 semana

    class Config:
        case_sensitive = True

settings = Settings()


#import secrets
#token: str = secrets.token_urlsafe(32)
