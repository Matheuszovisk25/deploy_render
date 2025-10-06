import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin
import os

URL_BASE = "http://vitibrasil.cnpuv.embrapa.br/"
TEST_URL = URL_BASE + "index.php"
PASTA_DESTINO = "data_scraping"

ROTAS = {
    "producao":        "opt_02",   # Produção
    "processamento":   "opt_03",   # Processamento
    "comercializacao": "opt_04",   # Comercialização

}
#Importação
SUB_ABAS_IMPORTACAO = {
    "subopt_01": "Vinhos de Mesa",
    "subopt_02": "Espumantes",
    "subopt_03": "Uvas frescas",
    "subopt_04": "Uvas passas",
    "subopt_05": "Suco de uva"
}
#Exportação
SUB_ABAS_EXPORTACAO = {
    "subopt_01": "Vinhos de Mesa",
    "subopt_02": "Espumantes",
    "subopt_03": "Uvas frescas",
    "subopt_04": "Suco de uva"

}

HEADERS = {"User-Agent": "Mozilla/5.0"}

def site_online(url=TEST_URL, timeout=10):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        return r.status_code == 200
    except Exception as e:
        print(f"🔌 Site indisponível: {e}")
        return False

def iniciar_navegador():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920x1080")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def encontrar_links_csv_com_selenium(url_pagina):
    navegador = iniciar_navegador()
    navegador.get(url_pagina)
    time.sleep(5)
    html = navegador.page_source
    navegador.quit()
    soup = BeautifulSoup(html, "html.parser")
    return [urljoin(URL_BASE, a["href"]) for a in soup.find_all("a", href=True) if a["href"].endswith(".csv")]

def baixar_csvs(links, pasta_destino):
    os.makedirs(pasta_destino, exist_ok=True)
    for url in links:
        nome_arquivo = os.path.basename(url)
        caminho = os.path.join(pasta_destino, nome_arquivo)
        if os.path.exists(caminho):
            print(f"↪️  Já existe: {nome_arquivo}")
            continue
        try:
            resposta = requests.get(url, headers=HEADERS)
            resposta.raise_for_status()
            with open(caminho, "wb") as f:
                f.write(resposta.content)
            print(f"✅ Baixado: {nome_arquivo}")
        except Exception as e:
            print(f"❌ Erro ao baixar {nome_arquivo}: {e}")

def coletar_csvs_se_online():
    print(f"🌐 Verificando disponibilidade de: {TEST_URL} ...")
    if not site_online():
        print("❌ Site da Embrapa Vitibrasil está offline. Tente novamente mais tarde.")
        return

    print("✅ Site online! Iniciando coleta de dados...\n")

    for nome_rota, codigo in ROTAS.items():
        url = f"{URL_BASE}index.php?opcao={codigo}"
        print(f"🔍 Coletando CSVs da rota '{nome_rota}' → {url}")
        try:
            links = encontrar_links_csv_com_selenium(url)
            if links:
                pasta = os.path.join(PASTA_DESTINO, nome_rota)
                for link in links:
                    print(f"🔗 {link}")
                baixar_csvs(links, pasta)
            else:
                print("⚠️ Nenhum CSV encontrado.")
        except WebDriverException as e:
            print(f"🚫 Erro Selenium ao acessar {nome_rota}: {e}")
        except Exception as e:
            print(f"❌ Falha inesperada: {e}")

    print("\n📁 Coletando sub-abas de 'importacao'...")
    for subopcao, nome_legivel in SUB_ABAS_IMPORTACAO.items():
        url = f"{URL_BASE}index.php?subopcao={subopcao}&opcao=opt_05"
        print(f"🔍 Coletando CSVs da sub-aba '{nome_legivel}' → {url}")
        try:
            links = encontrar_links_csv_com_selenium(url)
            if links:
                pasta = os.path.join(PASTA_DESTINO, "importacao", nome_legivel)
                for link in links:
                    print(f"🔗 {link}")
                baixar_csvs(links, pasta)
            else:
                print("⚠️ Nenhum CSV encontrado na sub-aba.")
        except WebDriverException as e:
            print(f"🚫 Erro Selenium ao acessar sub-aba '{nome_legivel}': {e}")
        except Exception as e:
            print(f"❌ Falha inesperada na sub-aba '{nome_legivel}': {e}")

    print("\n📁 Coletando sub-abas de 'exportacao'...")
    for subopcao, nome_legivel in SUB_ABAS_EXPORTACAO.items():
        url = f"{URL_BASE}index.php?subopcao={subopcao}&opcao=opt_06"
        print(f"🔍 Coletando CSVs da sub-aba '{nome_legivel}' → {url}")
        try:
            links = encontrar_links_csv_com_selenium(url)
            if links:
                pasta = os.path.join(PASTA_DESTINO, "exportacao", nome_legivel)
                for link in links:
                    print(f"🔗 {link}")
                baixar_csvs(links, pasta)
            else:
                print("⚠️ Nenhum CSV encontrado na sub-aba.")
        except WebDriverException as e:
            print(f"🚫 Erro Selenium ao acessar sub-aba '{nome_legivel}': {e}")
        except Exception as e:
            print(f"❌ Falha inesperada na sub-aba '{nome_legivel}': {e}")

    print("\n🎉 Coleta finalizada!")

if __name__ == "__main__":
    coletar_csvs_se_online()
