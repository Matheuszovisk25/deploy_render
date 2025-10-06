# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1.api import api_router  # <-- só o router

app = FastAPI(title="API - Tech Challenge_01 - Dados Vitivinicultura")

# CORS (ajuste allow_origins se quiser restringir)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prefixo V1
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def def_root():
    return {"mensagem": "Bem Vindo"}
