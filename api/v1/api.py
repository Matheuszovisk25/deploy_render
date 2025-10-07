from fastapi import APIRouter
from api.v1.endpoints import user, producao, processamento, comercializacao, importacao, exportacao, sintese

api_router = APIRouter()

@api_router.get("/")
async def def_root():
    return {"mensagem": "Bem Vindo"}

# ⬇️ sem prefix aqui (já existe no user.py)
api_router.include_router(user.router)

# Os demais mantêm o prefixo (se os módulos NÃO tiverem prefixo próprio)
api_router.include_router(producao.router, prefix='/producoes', tags=['produção'])
api_router.include_router(processamento.router, prefix='/processamentos', tags=['processamento'])
api_router.include_router(comercializacao.router, prefix='/comercializacoes', tags=['comercialização'])
api_router.include_router(importacao.router, prefix='/importacoes', tags=['importação'])
api_router.include_router(exportacao.router, prefix='/exportacoes', tags=['exportação'])
api_router.include_router(sintese.router, prefix='/sintese', tags=['previsao'])
