# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# suas rotas
from api.v1.api import api_router

# Base compartilhado e engine já criados no seu projeto
from core.settings import DBBaseModel
from core.database import engine  # usa o MESMO engine do projeto

# <<< IMPORTANTE: importe os modelos ANTES de create_all >>>
# isso registra todas as tabelas no metadata
import models.__all_models  # não precisa usar, só importar

app = FastAPI(title='API - Tech Challenge_01 - Dados Vitivinicultura')

# inclui suas rotas
app.include_router(api_router, prefix="/api/v1")

# CORS liberado (ajuste se quiser restringir)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# endpoint raiz (opcional)
@app.get("/")
async def root():
    return {"mensagem": "Bem Vindo"}

# cria as tabelas no startup (somente se ainda não existirem)
@app.on_event("startup")
async def on_startup():
    # como o engine é assíncrono, use run_sync para create_all síncrono
    async with engine.begin() as conn:
        await conn.run_sync(DBBaseModel.metadata.create_all)

# execução local (Render não usa este bloco; ele chama `uvicorn main:app`)
if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=10000, log_level='info', reload=True)
