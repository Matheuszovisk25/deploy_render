import asyncio
from core.database import engine
from core.settings import DBBaseModel
import models.user_model
import models.producao_model
import models.processamento_model
import models.importacao_model
import models.exportacao_model
import models.comercializacao_model
from data_process import load_all


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(DBBaseModel.metadata.drop_all)
        await conn.run_sync(DBBaseModel.metadata.create_all)

if __name__ == "__main__":
    print("\nCriando as tabelas...")
    load_all.ampola_loading(10)
    asyncio.run(create_tables())
    print("\nTabela criada com sucesso...")
    print("-------------------------------------------------------")
    print("\nInserindo dados nas tabelas...")
    load_all.ampola_loading(10)

    load_all.executar_tudo()
