from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from core.settings import settings, DBBaseModel

engine = create_async_engine(settings.DB_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session

# 👉 rode isso uma vez na inicialização
async def init_db():
    # importa todos os models para registrar as tabelas no metadata
    import models.__all_models  # garante que UserModel e cia. estejam carregados
    async with engine.begin() as conn:
        await conn.run_sync(DBBaseModel.metadata.create_all)
