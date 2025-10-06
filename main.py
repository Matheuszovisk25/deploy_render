from fastapi import FastAPI

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1 import api
from api.v1.api import api_router
from core.settings import settings

app = FastAPI(title='API - Tech Challenge_01 - Dados Vitivinicultura')
app.include_router(api_router, prefix="/api/v1")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def def_root():
    return {"mensagem": "Bem Vindo"}


if __name__ == '__main__':
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=10000,
                log_level='info', reload=True)
