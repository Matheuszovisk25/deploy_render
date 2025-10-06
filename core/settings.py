from pydantic_settings import BaseSettings
from sqlalchemy.orm import declarative_base

DBBaseModel = declarative_base()

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    DB_URL: str = "postgresql+asyncpg://postgres:admin@localhost:5432/techchallenge_db"
    #DB_URL: str = "postgresql+asyncpg://admin:mTeHvN2zSYQWgmqlNsCOuSoxKqtYzAGL@dpg-d0ua86idbo4c73ap46q0-a.oregon-postgres.render.com/db_techchalenge"
    JWT_SECRET_KEY: str = 'P7CpvrzKq7FH3xO5wtnNxJ84q2wGL28hNSS1pep2wrk'
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 semana

    class Config:
        case_sensitive = True

settings = Settings()


#import secrets
#token: str = secrets.token_urlsafe(32)
