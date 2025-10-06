import os
from data_process import (
    producao_clear,
    processamento_clear,
    comercializacao_clear,
    importacao_clear,
    exportacao_clear
)

import time
import sys

def ampola_loading(segundos: int):
    simbolos = ['⏳', '⌛', '⏱️', '🕰️']  # Ampola, relógios
    print(f"\n⏳ Aguardando {segundos} segundos...")
    for i in range(segundos):
        simbolo = simbolos[i % len(simbolos)]
        sys.stdout.write(f"\r{simbolo} Esperando... {segundos - i}s")
        sys.stdout.flush()
        time.sleep(1)
    #sys.stdout.write("\r✅ Pronto!              \n")
#Dados de Producao
def salvar_dados_prod():
    CAMINHO_CSV = "./data_process/data_scraping/producao/Producao.csv"
    if not os.path.exists(CAMINHO_CSV):
        print(f"❌ Arquivo não encontrado: {CAMINHO_CSV}")
    else:
        df_final = producao_clear.limpar_data_frame(CAMINHO_CSV)
        if not df_final.empty:
            producao_clear.salvar_no_banco(df_final)
        else:
            print("⚠️ Nenhum dado processado.")

# Dados Processamento
def salvar_dados_proc():
    # Caminho para o arquivo CSV
    CAMINHO_CSV = "./data_process/data_scraping/processamento/ProcessaViniferas.csv"

    if not os.path.exists(CAMINHO_CSV):
        print(f"❌ Arquivo não encontrado: {CAMINHO_CSV}")
    else:
        df_final = processamento_clear.limpar_data_frame(CAMINHO_CSV)
        if not df_final.empty:
            processamento_clear.salvar_no_banco(df_final)
        else:
            print("⚠️ Nenhum dado processado.")

def salvar_dados_com():
    # Caminho para o arquivo CSV
    CAMINHO_CSV = "./data_process/data_scraping/comercializacao/Comercio.csv"
    if not os.path.exists(CAMINHO_CSV):
        print(f"❌ Arquivo não encontrado: {CAMINHO_CSV}")
    else:
        df_final = comercializacao_clear.limpar_data_frame(CAMINHO_CSV)
        if not df_final.empty:
            comercializacao_clear.salvar_no_banco(df_final)
        else:
            print("⚠️ Nenhum dado processado.")

def salvar_dados_import():
    importacao_clear.limpar_dataframe()
def salvar_dados_export():
    exportacao_clear.limpar_dataframe()

def executar_tudo():
    print("\n🚀 Iniciando carregamento total dos dados no banco...\n")


    print("📂 Salvando os dados de produção...")
    salvar_dados_prod()

    print("\n📂 Salvando os dados de processamento:")
    salvar_dados_proc()

    print("\n📂 Salvando os dados de comercialização:")
    salvar_dados_com()

    print("\n📂 Salvando os dados de Importação:")
    salvar_dados_import()

    print("\n📂 Salvando os dados de Exportação:")
    salvar_dados_export()

    print("\n✅ Finalizado!")


