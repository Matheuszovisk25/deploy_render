from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.v1.api import api_router
from core.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # cria as tabelas se não existirem
    await init_db()
    yield

app = FastAPI(title="API - Tech Challenge_01 - Dados Vitivinicultura", lifespan=lifespan)
app.include_router(api_router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

@app.get("/")
async def def_root():
    return {"mensagem": "Bem Vindo"}
