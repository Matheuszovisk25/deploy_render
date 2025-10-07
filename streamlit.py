# app.py — Viticultura Dashboard (LOCAL) + Backtest de Previsões
# - Login → menu esquerdo (streamlit-option-menu) só após login
# - Páginas históricas (API local)
# - PREVISÕES: Backtest via API (/api/v1/sintese) OU via CSV
# - Hero com PNG local • Filtros dobráveis • Gráficos explicativos (sem toasts)

import io
import base64
import mimetypes
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import requests
from unidecode import unidecode

# ====== tenta importar statsmodels (ETS) ======
ETS_AVAILABLE = True
try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
except Exception as e:
    ETS_AVAILABLE = False
    ETS_IMPORT_ERR = str(e)

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

# ====== MENU lateral ======
try:
    from streamlit_option_menu import option_menu
except ImportError:
    st.error("Faltou instalar o menu. Rode:  pip install streamlit-option-menu")
    st.stop()

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Viticultura Dashboard", layout="wide", initial_sidebar_state="collapsed")

# ===================== CSS / UX =====================
def inject_css():
    st.markdown("""
    <style>
      :root { --brand:#e53935; }
      .metric-card{border-radius:16px;padding:14px 16px;
                   box-shadow:0 6px 18px rgba(0,0,0,.08);border:1px solid rgba(0,0,0,.06)}
      .metric-title{font-size:12px;color:#666;margin:0 0 6px 0;letter-spacing:.6px}
      .metric-value{font-size:28px;font-weight:800;margin:0;line-height:1}
      .metric-sub{font-size:12px;color:#8b8b8b;margin-top:4px}
      .empty{border:1px dashed rgba(0,0,0,.2); padding:18px;border-radius:14px; color:#666; text-align:center}
      .hero { position: relative; border-radius: 18px; overflow: hidden; min-height: 360px;
              display:flex; align-items:center; justify-content:center; color:white; }
      .hero::before { content:''; position:absolute; inset:0;
              background: linear-gradient(120deg, rgba(0,0,0,.65), rgba(0,0,0,.35)); z-index:1; }
      .hero .bg { position:absolute; inset:0; background-size: cover; background-position: center;
                  filter: brightness(.85); transform: scale(1.02); }
      .hero h1, .hero h2 { z-index:2; margin:0; text-align:center; }
      .hero h1 { font-size: 56px; letter-spacing: 8px; font-weight: 800; }
      .hero h2 { font-size: 20px; opacity:.95; margin-top: 8px;}
      .kpi { border-radius: 16px; padding:18px 20px; background:#e53935; color:white;
             box-shadow: 0 6px 18px rgba(229,57,53,.25); }
      .kpi h3 { font-size: 40px; margin:0; line-height:1; }
      .kpi p  { margin:0; opacity:.9; letter-spacing:.6px; }

      .story{border:1px solid #eee; border-radius:16px; padding:14px 16px; background:#ffffff; margin: 8px 0 6px 0;}
      .story h3{ margin-top:0; }
      .story .lead{ font-size:16px; color:#444 }
      .story ul{ margin: 8px 0 0 18px; }
      .story li{ margin: 4px 0; color:#222 }
      .callout{border-left:6px solid var(--brand); padding:12px 14px; border-radius:12px; background:#ffe9e9; color:#2a2a2a; margin-bottom:8px;}
      .spotlight{ margin:10px 0 0 0; padding:12px 14px; border-radius:12px; background:#fff5f4; color:#222; border:1px solid #ffd0cc; }

      .leftmenu{ border-right:1px solid #eee; padding-right:8px; margin-right:6px; }
      .brand-side{font-weight:800; font-size:18px; margin:4px 0 6px 4px}
      .logout-box{margin-top:10px; padding-top:8px; border-top:1px dashed #eee}
    </style>
    """, unsafe_allow_html=True)

def metric_card(title, value, sub=None):
    st.markdown(f"""
      <div class="metric-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        {f'<div class="metric-sub">{sub}</div>' if sub else ''}
      </div>
    """, unsafe_allow_html=True)

def human_compact(v, sufixo=""):
    try:
        n=float(v)
        if abs(n) >= 1_000_000: return f"{n/1_000_000:.0f} MI{sufixo}"
        if abs(n) >= 1_000: return f"{n/1_000:.0f} K{sufixo}"
        return f"{n:.0f}{sufixo}"
    except: return "—"

inject_css()

# -----------------------------------------------------------------------------
# API LOCAL
# -----------------------------------------------------------------------------
API_BASE = "https://https://deploy-render-7wwi.onrender.com/api/v1"
LOGIN_URL  = f"{API_BASE}/users/login"
SIGNUP_URL = f"{API_BASE}/users/signup"

PAGES = {
    "Início": {"endpoint": None, "desc": "Visão geral e destaques"},
    "Importação": {"endpoint": "importacoes", "desc": "Entradas (país de origem, produtos)"},
    "Exportação": {"endpoint": "exportacoes", "desc": "Destinos e valores exportados"},
    "Produção": {"endpoint": "producoes", "desc": "Volume por ano e produto"},
    "Processamento": {"endpoint": "processamentos", "desc": "Etapas e capacidade"},
    "Comercialização": {"endpoint": "comercializacoes", "desc": "Mercado interno"},
    "Previsões": {"endpoint": None, "desc": "Backtest ETS via API /sintese ou CSV"},
}
PAGE_NAMES = list(PAGES.keys())

# ===== Fontes para “in-text” (links)
SRC = {
    "OIV_2023": "https://www.oiv.int/sites/default/files/2024-04/OIV_STATE_OF_THE_WORLD_VINE_AND_WINE_SECTOR_IN_2023.pdf",
    "OIV_2024": "https://www.oiv.int/sites/default/files/2025-04/OIV-State_of_the_World_Vine-and-Wine-Sector-in-2024.pdf",
    "OEC_BRA_WINE_2023": "https://oec.world/en/profile/bilateral-product/wine/reporter/bra",
    "WITS_BRA_220421_2023": "https://wits.worldbank.org/trade/comtrade/en/country/BRA/year/2023/tradeflow/Imports/partner/ALL/product/220421",
    "REUTERS_OIV_221mhl_2023": "https://www.reuters.com/markets/commodities/global-wine-demand-drops-27-year-low-high-prices-hit-2024-04-25/",
}
SPOTLIGHTS = {
    "Produção": ("🇧🇷 Em 2023, o Brasil foi o **3º maior produtor** de vinhos da América do Sul, "
                 "com cerca de **3,6 mhl** ([OIV 2023]({})).".format(SRC["OIV_2023"])),
    "Exportação": ("🌍 As exportações brasileiras ainda são enxutas e concentradas, com espaço para nichos premium "
                   "([OEC 2023]({})).".format(SRC["OEC_BRA_WINE_2023"])),
    "Importação": ("📦 O Brasil figura entre os **maiores compradores** da região; fornecedores líderes: Chile, UE e Argentina "
                   "([WITS/Comtrade 2023]({})).".format(SRC["WITS_BRA_220421_2023"])),
    "Comercialização": ("🛒 Mesmo com **consumo mundial em queda** em 2023, o Brasil manteve tração em ocasiões de celebração "
                        "([Reuters/OIV]({})).".format(SRC["REUTERS_OIV_221mhl_2023"])),
    "Processamento": ("⚙️ Safra 2024 marcada por clima extremo exige eficiência de planta e priorização de rótulos core "
                      "([OIV 2024]({})).".format(SRC["OIV_2024"])),
}
LONG_STORIES = {
    "Início": (
        "O setor de vinhos no Brasil viveu um ciclo misto recente. Em **2023**, a produção nacional cresceu para "
        "**3,6 mhl**, superando o ano anterior e a média de 5 anos, segundo a [OIV 2023]({oiv23}). Em **2024**, "
        "eventos climáticos reduziram colheitas no mundo e pressionaram operações, conforme a [OIV 2024]({oiv24}). "
        "Este painel organiza os movimentos de produção, comércio exterior, mercado interno e gargalos operacionais "
        "para transformar dado em decisão."
    ).format(oiv23=SRC["OIV_2023"], oiv24=SRC["OIV_2024"]),
    "Produção": (
        "A safra de **2023** marcou um ponto alto recente: **3,6 mhl** (**+12% a/a**; **+31%** vs. média 2018–2022), "
        "colocando o Brasil como **3º maior produtor** da América do Sul — dados da [OIV 2023]({oiv23}). "
        "Em **2024**, a OIV estima **~2,1 mhl** para o Brasil (**−41% a/a**), refletindo choque climático "
        "([OIV 2024]({oiv24})). Estoques, mix de produtos e contratos com viticultores tornam-se chaves para suavizar "
        "a volatilidade nas próximas safras."
    ).format(oiv23=SRC["OIV_2023"], oiv24=SRC["OIV_2024"]),
    "Exportação": (
        "As exportações seguem **em desenvolvimento**: em **2023** somaram **~US$ 11,6 milhões**, com maior presença "
        "em **Paraguai, Estados Unidos e Haiti**, segundo o [OEC 2023]({oec}). A pauta enxuta e sensível a câmbio/frete "
        "explica oscilações anuais; o foco está em nichos onde o Brasil é competitivo (espumantes, climas frios), "
        "marcas com história de origem e ativação on-trade em destinos de fronteira."
    ).format(oec=SRC["OEC_BRA_WINE_2023"]),
    "Importação": (
        "O Brasil é um **mercado de importados** relevante. Em **2023**, as compras externas de vinho não espumante "
        "(HS 2204.21) foram de **147,1 milhões de litros** por **US$ 446,9 milhões**, com **Chile, Argentina, Portugal, "
        "Itália e França** entre os principais fornecedores — fonte: [WITS/Comtrade 2023]({wits}). Para as vinícolas "
        "locais, os importados são referencial de preço/qualidade e pressão competitiva, pedindo diferenciação de "
        "origem, comunicação de frescor e gastronomia brasileira."
    ).format(wits=SRC["WITS_BRA_220421_2023"]),
    "Comercialização": (
        "Enquanto o **consumo global** caiu para **221 mhl em 2023** (nível mais baixo desde 1996), de acordo com a "
        "[OIV; cobertura Reuters]({rt}), o mercado brasileiro manteve bom dinamismo em ocasiões de celebração e canais "
        "digitais mais maduros. Para sustentar a trajetória: sortimento por ocasião, educação simples no PDV e promoções "
        "que preservem preço médio/margem."
    ).format(rt=SRC["REUTERS_OIV_221mhl_2023"]),
    "Processamento": (
        "A safra **2024** exigiu replanejamento de **moagem/fermentação/estabilização**: com menos matéria-prima, a "
        "estratégia tende a priorizar labels core e alongar estoques estratégicos. A [OIV 2024]({oiv4}) ressalta o "
        "efeito do clima na oferta global. Operacionalmente: manutenção preventiva (tanques e frio), revisão de "
        "fornecimento e foco em vinhos de **maior contribuição por litro**."
    ).format(oiv4=SRC["OIV_2024"]),
}
PAGE_SOURCE = {
    "Produção": ("OIV 2023/2024", SRC["OIV_2023"]),
    "Exportação": ("OEC 2023", SRC["OEC_BRA_WINE_2023"]),
    "Importação": ("WITS/Comtrade 2023 (HS 2204.21)", SRC["WITS_BRA_220421_2023"]),
    "Comercialização": ("OIV 2023 (consumo) – Reuters", SRC["REUTERS_OIV_221mhl_2023"]),
    "Processamento": ("OIV 2024", SRC["OIV_2024"]),
    "Início": ("OIV 2023/2024", SRC["OIV_2024"]),
}

# -----------------------------------------------------------------------------
# Auth, cache e helpers
# -----------------------------------------------------------------------------
if "token" not in st.session_state: st.session_state.token = None
if "page" not in st.session_state: st.session_state.page = "Início"

def render_intro_navigation():
    st.markdown("""
<div class="story">
  <h3>Como navegar pelo painel</h3>
  <p class="lead">
    O Brasil tem <b>potencial real de ganho</b> no setor do vinho. Mesmo competindo com mercados <b>consolidados</b>,
    avanços em <b>parcerias comerciais</b>, eficiência de <b>processamento</b> e leitura de dados sustentam a expansão.
    As seções abaixo mostram <b>onde estamos</b> e <b>para onde podemos ir</b>.
  </p>

  <div class="callout"><b>O que cada seção mostra (e quais gráficos usamos)</b></div>
  <ul style="margin:8px 0 0 18px;">
    <li><b>Produção</b> — volume e trajetória recente.
      <div><i>Gráficos:</i> Linha temporal, Barras por ano, Top produtos, Pareto (concentração).</div>
    </li>
    <li><b>Importação</b> — pressão competitiva externa (origens e valores).
      <div><i>Gráficos:</i> Linha/Barras por ano, Top países, Pareto, Comparação entre anos.</div>
    </li>
    <li><b>Exportação</b> — onde o Brasil performa melhor no exterior.
      <div><i>Gráficos:</i> Linha/Barras, Top destinos, Pareto, Comparação (ganhos/perdas por país).</div>
    </li>
    <li><b>Processamento</b> — capacidade e gargalos operacionais.
      <div><i>Gráficos:</i> Linha (capacidade vs. uso), Barras por etapa, Pareto de etapas/insumos.</div>
    </li>
    <li><b>Comercialização</b> — dinâmica do mercado interno e itens que puxam resultado.
      <div><i>Gráficos:</i> Linha/Barras (mudança de nível), Top produtos, Pareto, Comparação de anos.</div>
    </li>
    <li><b>Previsões</b> — horizonte de 5 anos e qualidade do modelo.
      <div><i>Gráficos:</i> Backtest ETS (Real × Previsto com MAE, WAPE, sMAPE) e Série histórica + <b>Previsão 5 anos</b>.</div>
    </li>
  </ul>

  <div class="callout" style="margin-top:14px;"><b>Backtest ETS — o que é e como interpretar</b></div>
  <div class="spotlight">
    <b>O que é:</b> treinamos o modelo ETS (Holt-Winters com tendência amortecida) usando apenas anos anteriores e
    testamos em anos “segurados”. Assim medimos se o modelo <i>generaliza</i> para o futuro.
  </div>

  <ul style="margin:10px 0 0 18px;">
    <li><b>MAE</b> — Erro Absoluto Médio, em <i>unidades do indicador</i> (litros, R$, etc.).
      <div>Interpretação: “em média, erramos <i>X</i> unidades por ano”. Fácil de entender; não é percentual.</div>
    </li>
    <li><b>WAPE</b> — Erro Absoluto Percentual Ponderado pelo <i>total real</i>.
      <div>Interpretação: “o modelo erra ~<i>X%</i> do total do período”. Bom para comparar entre séries de tamanhos diferentes.</div>
    </li>
    <li><b>sMAPE</b> — Erro Percentual Médio <i>simétrico</i> por ponto.
      <div>Interpretação: erro médio relativo por ano. É mais estável que MAPE quando há valores próximos de zero.</div>
    </li>
  </ul>

  <div class="spotlight" style="margin-top:10px;">
    <b>Como usar juntos:</b> use <b>MAE</b> para impacto operacional (R$/L),
    <b>WAPE</b> para dizer “quão bom” no agregado do período e <b>sMAPE</b> para a qualidade por ano.
  </div>

  <ul style="margin:10px 0 0 18px;">
    <li><b>Regras de bolso</b> (varia por contexto): WAPE &lt; 20% = bom; &lt; 10% = muito bom. sMAPE &lt; 20% costuma ser sólido.</li>
    <li><b>Boas práticas</b>: compare sempre <i>modelos/versões</i> na mesma métrica; garanta anos suficientes de treino; verifique outliers.</li>
  </ul>

  <div class="spotlight" style="margin-top:10px;">
    💡 <b>Dica de priorização:</b> a <b>Curva de Pareto</b> mostra quantos itens explicam ~80% do total.
    Se poucos itens concentram o resultado, foque neles antes de expandir o portfólio.
  </div>
</div>
""", unsafe_allow_html=True)

def _truncate(s: str, n: int = 16) -> str:
    s = str(s)
    return s if len(s) <= n else s[: max(0, n - 1)] + "…"

def _label_pareto_items(pf: pd.DataFrame, max_chars: int = 16) -> pd.DataFrame:
    """
    Recebe o df do Pareto (colunas: item, valor, share, cum_share, rank)
    e devolve um df com a coluna 'label' (nome encurtado p/ eixo X) + customdata p/ hover.
    Mantém a ordem pelo 'rank'.
    """
    pf = pf.sort_values("rank").copy()
    pf["label"] = pf["item"].astype(str).map(lambda x: _truncate(x, max_chars))
    # embute dados extras para hover
    pf["_item_full"] = pf["item"].astype(str)
    pf["_rank"] = pf["rank"].astype(int)
    pf["_share_pct"] = (pf["share"] * 100).round(1)
    pf["_cum_pct"] = (pf["cum_share"] * 100).round(1)
    return pf


def autenticar_usuario(email, senha):
    try:
        r = requests.post(LOGIN_URL, data={"username": email, "password": senha}, timeout=10)
        r.raise_for_status()
        return r.json()["access_token"]
    except Exception as e:
        st.error("Falha no login: " + str(e))
        return None

def cadastrar_usuario(name, surname, email, password):
    try:
        r = requests.post(SIGNUP_URL, json={"name": name, "surname": surname, "email": email, "password": password}, timeout=10)
        if r.status_code == 400 and "already registered" in str(r.json().get("detail","")).lower():
            st.error("Este e-mail já está cadastrado. Tente fazer login.")
            return
        r.raise_for_status()
        st.success("Usuário criado com sucesso! Entrando…")
        token = autenticar_usuario(email, password)
        if token:
            st.session_state.token = token
            st.rerun()
    except Exception as e:
        st.error(f"Erro ao cadastrar: {e}")

def _auth_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}

@st.cache_data(show_spinner=False)
def carregar_dados(endpoint, token_key):
    url = f"{API_BASE}/{endpoint}/"
    headers = _auth_headers()
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    return pd.DataFrame(r.json())

def carregar_dados_com_silencio(endpoint):
    try:
        return carregar_dados(endpoint, token_key=st.session_state.token or "anon")
    except Exception as e:
        st.error(f"Erro ao carregar dados de {endpoint}: {e}")
        return pd.DataFrame()

# ===== Helpers comuns =====
def detectar_coluna_produto(df: pd.DataFrame):
    for col in ["produto", "produto_nome", "produto_tipo"]:
        if col in df.columns:
            return col
    return None

def aplicar_filtros(df: pd.DataFrame, produto_col: str, busca, anos, produtos):
    df = df.copy()
    if produtos and produto_col and produto_col in df.columns:
        df = df[df[produto_col].isin(produtos)]
    if anos and "ano" in df.columns and isinstance(anos, (tuple, list)) and len(anos) == 2:
        anos_num = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")
        df = df[anos_num.between(int(anos[0]), int(anos[1]))]
    if busca:
        busca_proc = unidecode(str(busca).lower())
        mask = pd.Series(False, index=df.index)
        if produto_col and produto_col in df.columns:
            mask = mask | df[produto_col].astype(str).str.lower().map(unidecode).str.contains(busca_proc, na=False)
        if "pais" in df.columns:
            mask = mask | df["pais"].astype(str).str.lower().map(unidecode).str.contains(busca_proc, na=False)
        df = df[mask]
    return df

# ---------- Keys únicas para evitar DuplicateElementId ----------
def _key_from(parts):
    return "plt_" + "_".join(str(p).strip().lower().replace(" ", "_") for p in parts if p is not None)

def chart(fig, *, key_parts):
    st.plotly_chart(fig, use_container_width=True, key=_key_from(key_parts))

# ---------- Helpers para gráficos ----------
def set_title_and_subtitle(fig, title, subtitle=None):
    if subtitle:
        fig.update_layout(title={'text': f"{title}<br><sup>{subtitle}</sup>"},
                          margin=dict(t=80))
    else:
        fig.update_layout(title=title)

def annotate_line_peaks(fig, df_xy, xcol, ycol):
    if df_xy.empty: return
    max_row = df_xy.loc[df_xy[ycol].idxmax()]
    min_row = df_xy.loc[df_xy[ycol].idxmin()]
    fig.add_annotation(x=max_row[xcol], y=max_row[ycol],
                       text=f"Pico: {human_compact(max_row[ycol])}",
                       showarrow=True, arrowhead=2, ax=0, ay=-40)
    if min_row[xcol] != max_row[xcol]:
        fig.add_annotation(x=min_row[xcol], y=min_row[ycol],
                           text=f"Vale: {human_compact(min_row[ycol])}",
                           showarrow=True, arrowhead=2, ax=0, ay=40)


# -----------------------------------------------------------------------------
# Landing (PNG local no herói)
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.resolve()
HERO_BG_URL = "imagem_vinho.png"
FALLBACK_HERO_URL = "https://images.unsplash.com/photo-1541542684-4a6c80b47cce?q=80&w=1920&auto=format&fit=crop"

def _bg_css_from_source(src: str) -> str:
    if not src: return f".hero .bg{{background-image:url('{FALLBACK_HERO_URL}') !important;}}"
    if str(src).lower().startswith(("http://", "https://")):
        return f".hero .bg{{background-image:url('{src}') !important;}}"
    p = Path(src)
    if not p.is_absolute(): p = BASE_DIR / p
    if p.exists():
        mime, _ = mimetypes.guess_type(p.name); mime = mime or "image/png"
        b64 = base64.b64encode(p.read_bytes()).decode()
        return f'.hero .bg{{background-image:url("data:{mime};base64,{b64}") !important;}}'
    return f".hero .bg{{background-image:url('{FALLBACK_HERO_URL}') !important;}}"

def fmt_mi(v, sufixo=""):
    try:
        n = float(v)
        if abs(n) >= 1_000_000: return f"{int(round(n/1_000_000,0))} MI{sufixo}"
        if abs(n) >= 1_000: return f"{int(round(n/1_000,0))} K{sufixo}"
        return f"{int(round(n,0))}{sufixo}"
    except Exception:
        return "—"

def resumo_metrico_home():
    df_exp = carregar_dados_com_silencio("exportacoes")
    df_pro = carregar_dados_com_silencio("producoes")
    total_exp = df_exp["valor"].sum() if "valor" in df_exp.columns else None
    total_pro_l = df_pro["quantidade"].sum() if "quantidade" in df_pro.columns else None
    fallback_exp_usd = 96_000_000
    fallback_litros  = 81_000_000
    ranking_txt = "15º MAIOR PRODUTOR DO MUNDO"
    exp_txt = fmt_mi(total_exp or fallback_exp_usd, " US$")
    prod_txt = fmt_mi(total_pro_l or fallback_litros, "")
    return exp_txt, ranking_txt, prod_txt

def page_home():
    st.markdown(
        """
        <div class="hero">
            <div class="bg"></div>
            <div style="z-index:2;">
                <h1>BRASIL NO<br>CENÁRIO MUNDIAL</h1>
                <h2>Viticultura — dados oficiais • análise interativa</h2>
            </div>
        </div>
        """, unsafe_allow_html=True
    )
    st.markdown(f"<style>{_bg_css_from_source(HERO_BG_URL)}</style>", unsafe_allow_html=True)

    exp_txt, ranking_txt, prod_txt = resumo_metrico_home()
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="kpi"><h3>{exp_txt}</h3><p>EXPORTADOS</p></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="kpi"><h3>{ranking_txt.split()[0]}</h3><p>{" ".join(ranking_txt.split()[1:])}</p></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="kpi"><h3>{prod_txt}</h3><p>LITROS PRODUZIDOS</p></div>', unsafe_allow_html=True)
    st.markdown(" ")
    render_intro_navigation()


# -----------------------------------------------------------------------------
# Storytelling + gráficos (histórico)
# -----------------------------------------------------------------------------
def _years_info(df):
    if "ano" not in df.columns: return None
    anos = pd.to_numeric(df["ano"], errors="coerce").dropna().astype(int)
    if anos.empty: return None
    return dict(min=int(anos.min()), max=int(anos.max()), uniq=sorted(anos.unique()))

def _yoy(df, metric):
    if "ano" not in df.columns or metric not in df.columns: return None
    anos = pd.to_numeric(df["ano"], errors="coerce").dropna().astype(int)
    if anos.nunique() < 2: return None
    y_sorted = sorted(anos.unique())
    y_prev, y_now = y_sorted[-2], y_sorted[-1]
    v_prev = df.loc[anos==y_prev, metric].sum()
    v_now  = df.loc[anos==y_now, metric].sum()
    if v_prev == 0: return None
    return dict(prev_year=y_prev, year=y_now, delta=v_now-v_prev, rate=(v_now-v_prev)/v_prev, now=v_now)

def _top_group(df, group_col, metric, n=5):
    if group_col in df.columns and metric in df.columns and not df.empty:
        t = (df.groupby(group_col)[metric].sum()
             .sort_values(ascending=False).head(n))
        return t
    return pd.Series(dtype=float)

def make_story(page_name: str, df: pd.DataFrame, metric_col: str, produto_col):
    yi = _years_info(df); yoy = _yoy(df, metric_col)
    top_prod = _top_group(df, produto_col, metric_col, n=5) if produto_col else pd.Series(dtype=float)
    top_pais = _top_group(df, "pais", metric_col, n=5) if "pais" in df.columns else pd.Series(dtype=float)

    lead_parts = []
    if yi: lead_parts.append(f"Cobrimos **{yi['min']}–{yi['max']}**.")
    total = df.get(metric_col, pd.Series(dtype=float)).sum()
    lead_parts.append(f"No período filtrado, somamos **{human_compact(total)}** em **{metric_col}**.")
    if yoy:
        sinal = "↑" if yoy["rate"]>=0 else "↓"
        lead_parts.append(f"De {yoy['prev_year']} para {yoy['year']} houve **{sinal} {abs(yoy['rate']*100):.1f}%**.")
    lead = " ".join(lead_parts)

    bullets = []
    if produto_col and not top_prod.empty:
        p0, v0 = top_prod.index[0], top_prod.iloc[0]
        share0 = v0/total if total else 0
        bullets.append(f"**Produto líder:** {p0} ({human_compact(v0)} • {share0*100:.1f}% do total).")
    if not top_pais.empty:
        p1, v1 = top_pais.index[0], top_pais.iloc[0]
        sh1 = v1/total if total else 0
        bullets.append(f"**Mercado-chave:** {p1} ({human_compact(v1)} • {sh1*100:.1f}%).")
    if not bullets:
        bullets.append("Distribuição pulverizada sem líderes evidentes.")

    TIT = {
        "Exportação": ("O que impulsiona as exportações", "Quem compra, o que vende e como evolui no tempo."),
        "Importação": ("O que puxa as importações", "Principais origens e produtos, com foco na tendência."),
        "Produção": ("Como está a produção", "Ritmo, produtos campeões e concentração do portfólio."),
        "Comercialização": ("Termômetro do mercado interno", "Variação anual e itens que mais giram."),
        "Processamento": ("Panorama do processamento", "Capacidade, etapas e evolução."),
    }.get(page_name, ("História dos dados", "Resumo narrativo para orientar a leitura."))

    st.markdown(f"""
    <div class="story">
      <h3>{TIT[0]}</h3>
      <p class="lead">{TIT[1]}</p>
      <div class="callout">{lead}</div>
      <ul>
        {''.join([f"<li>{b}</li>" for b in bullets])}
      </ul>
    </div>
    """, unsafe_allow_html=True)

    spot_text = SPOTLIGHTS.get(page_name)
    if spot_text: st.markdown(f'<div class="spotlight">📌 {spot_text}</div>', unsafe_allow_html=True)
    long_txt = LONG_STORIES.get(page_name)
    if long_txt: st.markdown(long_txt)

# -----------------------------------------------------------------------------
# MENU ESQUERDO (após login)
# -----------------------------------------------------------------------------
def render_left_menu():
    with st.container():
        st.markdown('<div class="leftmenu">', unsafe_allow_html=True)
        st.markdown('<div class="brand-side">🍇 Viticultura</div>', unsafe_allow_html=True)

        names = PAGE_NAMES
        current = st.session_state.get("page", "Início")
        default_index = names.index(current) if current in names else 0

        selected = option_menu(
            menu_title="Navegação",
            options=names,
            icons=["house", "box-arrow-in-down", "box-arrow-up", "graph-up", "gear", "cart", "activity"],
            default_index=default_index,
            orientation="vertical",
            styles={
                "container": {"padding": "0 0 8px 0", "background-color": "rgba(255,255,255,0.00)"},
                "icon": {"color": "#e53935", "font-size": "16px"},
                "nav-link": {"font-size": "15px", "padding":"8px 12px", "margin":"2px 0", "border-radius":"10px",
                             "--hover-color": "rgba(229,57,53,.12)"},
                "nav-link-selected": {"background-color": "#e53935"},
            },
        )
        st.session_state.page = selected

        st.markdown('<div class="logout-box">', unsafe_allow_html=True)
        if st.button("Logout", type="primary", use_container_width=True):
            st.session_state.token = None
            st.session_state.page = "Início"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

def filter_panel(produto_col, df):
    with st.expander("🔎 Filtros", expanded=True):
        ctop = st.columns([3, 1])
        with ctop[0]:
            busca = st.text_input("Buscar produto ou país (ignora acento)", value=st.session_state.get("busca", ""))
            st.session_state["busca"] = busca
        with ctop[1]:
            st.caption(" ")
        anos = None
        if "ano" in df.columns:
            try:
                anos_disponiveis = sorted(pd.to_numeric(df["ano"], errors="coerce").dropna().astype(int).unique())
                if len(anos_disponiveis) > 0:
                    ano_min, ano_max = int(min(anos_disponiveis)), int(max(anos_disponiveis))
                    anos_default = st.session_state.get("anos", (ano_min, ano_max))
                    anos = st.slider("Ano (intervalo)", min_value=ano_min, max_value=ano_max, value=anos_default)
                    st.session_state["anos"] = anos
            except Exception:
                pass
        produtos = []
        if produto_col and produto_col in df.columns:
            try:
                prods_default = st.session_state.get("produtos", [])
                produtos = st.multiselect("Produto(s)",
                            sorted(df[produto_col].dropna().astype(str).unique()),
                            default=prods_default)
                st.session_state["produtos"] = produtos
            except Exception:
                produtos = []
    return st.session_state.get("busca"), st.session_state.get("anos"), st.session_state.get("produtos")

# -----------------------------------------------------------------------------
# FUNÇÕES DO BACKTEST (compartilhadas entre API/CSV)
# -----------------------------------------------------------------------------
def fit_ets(y_train: pd.Series):
    y_train = np.asarray(y_train, dtype=float)
    y_train = np.maximum(y_train, 0.0)
    model = ExponentialSmoothing(
        y_train,
        trend="add",
        damped_trend=True,  # tendência amortecida
        seasonal=None,
        initialization_method="estimated",
    )
    fitted = model.fit(optimized=True, use_brute=True)
    return fitted

def rolling_backtest(df_year_val: pd.DataFrame, start_year: int, end_year: int) -> pd.DataFrame:
    out_rows = []
    for ano_t in range(int(start_year), int(end_year) + 1):
        train = df_year_val[df_year_val["ano"] < ano_t].copy()
        test  = df_year_val[df_year_val["ano"] == ano_t].copy()
        if len(train) < 4 or test.empty:
            continue

        fitted = fit_ets(train["valor"].values)
        pred = float(fitted.forecast(1)[0])
        pred = max(pred, 0.0)  # sem negativos

        out_rows.append({"ano": ano_t, "previsto_bruto": pred, "real": float(test["valor"].values[0])})

    return pd.DataFrame(out_rows)

# -----------------------------------------------------------------------------
# Fluxo principal
# -----------------------------------------------------------------------------
# 1) Sem login
if not st.session_state.token:
    st.markdown("<h2 style='text-align:center'>🔐 Faça login para continuar</h2>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Entrar", "Cadastrar"])
    with tab1:
        st.markdown("### Login")
        with st.form("login_form"):
            email = st.text_input("E-mail", placeholder="Digite seu e-mail")
            senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            if st.form_submit_button("Entrar"):
                token = autenticar_usuario(email, senha)
                if token:
                    st.session_state.token = token
                    st.success("Login realizado com sucesso!")
                    st.rerun()
    with tab2:
        st.markdown("### Criar Conta")
        with st.form("signup_form"):
            name = st.text_input("Nome", placeholder="Seu nome")
            surname = st.text_input("Sobrenome", placeholder="Seu sobrenome")
            email = st.text_input("E-mail", placeholder="Digite um e-mail válido")
            password = st.text_input("Senha", type="password", placeholder="Crie uma senha")
            if st.form_submit_button("Cadastrar"):
                cadastrar_usuario(name, surname, email, password)

# 2) Com login: menu esquerdo + conteúdo
else:
    col_menu, col_content = st.columns([0.22, 0.78], gap="large")

    with col_menu:
        render_left_menu()

    with col_content:
        page = st.session_state.get("page", "Início")

        # ===== Início
        if page == "Início":
            page_home()
            st.stop()

        # ===== Previsões (Backtest via API ou CSV)
        # ===== Previsões (Backtest via API ou CSV) + botão de Previsão 5 anos
        if page == "Previsões":
            st.title("Previsões — Backtest (ETS/Holt-Winters)")
            if not ETS_AVAILABLE:
                st.error(
                    "statsmodels não está disponível (necessário para ETS/Holt-Winters).\n\n"
                    f"Erro de importação: {ETS_IMPORT_ERR}\n\n"
                    "Instale com:  \n"
                    "`pip install statsmodels`"
                )
                st.stop()
            
            modo = st.radio("Fonte de dados para o backtest", ["API (/sintese)", "CSV"], horizontal=True)

            # ---------- MODO API (/sintese)
            if modo == "API (/sintese)":
                api_url = st.text_input("URL da API de síntese anual",
                        value=f"{API_BASE}/sintese/")

                @st.cache_data(show_spinner=False)
                def carregar_sintese(api_url: str, ano_min=None, ano_max=None) -> pd.DataFrame:
                    params = {}
                    if ano_min is not None: params["ano_min"] = int(ano_min)
                    if ano_max is not None: params["ano_max"] = int(ano_max)
                    r = requests.get(api_url, headers=_auth_headers(), params=params, timeout=30)
                    r.raise_for_status()
                    return pd.DataFrame(r.json())

                try:
                    df_s = carregar_sintese(api_url)
                except Exception as e:
                    st.error(f"Erro ao consultar a API: {e}")
                    st.stop()

                if df_s.empty or "ano" not in df_s.columns:
                    st.error("API não retornou dados válidos (precisa ao menos de 'ano').")
                    st.stop()

                # Métricas possíveis
                cand_cols = [c for c in df_s.columns if c != "ano" and pd.api.types.is_numeric_dtype(df_s[c])]
                prior = ["producao_total","processamento_total","comercializacao_total",
                        "importacao_qtd","importacao_valor","exportacao_qtd","exportacao_valor"]
                ord_cols = [c for c in prior if c in cand_cols] + [c for c in cand_cols if c not in prior]
                if not ord_cols:
                    st.error("Não encontrei colunas numéricas elegíveis na resposta da API.")
                    st.stop()

                col_val = st.selectbox("Métrica para modelar", ord_cols, index=0)

                serie = df_s[["ano", col_val]].dropna().copy()
                serie["ano"] = pd.to_numeric(serie["ano"], errors="coerce").astype("Int64").dropna().astype(int)
                serie = serie.groupby("ano", as_index=False)[col_val].sum().sort_values("ano")
                serie.columns = ["ano", "valor"]

                # ------- Backtest (inalterado: exige ≥ 8 pontos)
                if len(serie) < 8:
                    st.error("Poucos anos. Recomendo ≥ 8 pontos para um backtest confiável.")
                    st.stop()

                anos = serie["ano"].tolist()
                c1, c2 = st.columns(2)
                ini = c1.number_input("Ano inicial do TESTE", min_value=int(anos[1]), max_value=int(anos[-1]), value=int(anos[len(anos)//2]))
                fim = c2.number_input("Ano final do TESTE",   min_value=int(ini),       max_value=int(anos[-1]), value=int(anos[-1]))

                opt_cb, opt_lin = st.columns(2)
                usar_fator = opt_cb.checkbox("Aplicar correção de viés (fator soma real/soma previsto)", value=True)
                usar_linear = opt_lin.checkbox("Aplicar calibração linear a + b·previsto (além do fator)", value=False)

                if st.button("🧪 Rodar Backtest (API)", key="run_backtest_api"):
                    if serie["ano"].min() >= ini:
                        st.error("Precisa existir ao menos UM ano antes do início do teste para treinar o primeiro modelo.")
                        st.stop()

                    back = rolling_backtest(serie, ini, fim)
                    if back.empty:
                        st.error("Nada para testar nesse intervalo (verifique os anos informados).")
                        st.stop()

                    prev = back["previsto_bruto"].values.astype(float)
                    real = back["real"].values.astype(float)

                    fator = (real.sum() / max(prev.sum(), 1e-9)) if usar_fator else 1.0
                    prev_corr = prev * fator

                    calib = None
                    if usar_linear:
                        X = prev_corr.reshape(-1, 1)
                        lr = LinearRegression()
                        lr.fit(X, real)
                        prev_corr = lr.predict(X)
                        calib = (float(lr.intercept_), float(lr.coef_[0]))

                    mae   = mean_absolute_error(real, prev_corr)
                    wape_ = float(np.sum(np.abs(real - prev_corr)) / max(np.sum(np.abs(real)), 1e-9))
                    def _smape(y, yhat):
                        y, yhat = np.asarray(y), np.asarray(yhat)
                        denom = np.abs(y) + np.abs(yhat); denom[denom == 0] = 1e-9
                        return float(np.mean(2 * np.abs(y - yhat) / denom))
                    smap  = _smape(real, prev_corr)

                    out = pd.DataFrame({"ano": back["ano"], "real": real, "previsto": prev_corr})
                    out["erro_abs"] = (out["real"] - out["previsto"]).abs()
                    out["erro_%"]   = (out["real"] - out["previsto"]) / np.where(out["real"]==0, 1e-9, out["real"]) * 100

                    m1, m2, m3 = st.columns(3)
                    m1.metric("MAE", f"{mae:,.0f}")
                    m2.metric("WAPE", f"{wape_*100:,.2f}%")
                    m3.metric("sMAPE", f"{smap*100:,.2f}%")
                    if usar_fator:
                        st.caption(f"Fator de viés aplicado: **{fator:.3f}**")
                    if calib is not None:
                        st.caption(f"Calibração linear: **previsto = {calib[0]:.2f} + {calib[1]:.3f} × previsto_corrigido**")

                    st.subheader(f"Tabela — Backtest ({col_val})")
                    st.dataframe(out, use_container_width=True)

                    fig = px.line(out, x="ano", y="real", markers=True,
                                title=f"Backtest {int(ini)}–{int(fim)} — Real vs Previsto (corrigido) • {col_val}")
                    fig.add_scatter(x=out["ano"], y=out["previsto"], mode="lines+markers", name="Previsto")
                    chart(fig, key_parts=["previsoes", "api_backtest", col_val, ini, fim])

                    st.download_button(
                        "📥 Baixar CSV do backtest",
                        out.to_csv(index=False).encode("utf-8"),
                        file_name=f"backtest_{col_val}_{int(ini)}_{int(fim)}.csv",
                        mime="text/csv"
                    )

                # ------- 🔮 Previsão 5 anos (independente do backtest)
                st.markdown("---")
                st.subheader("🔮 Previsão (5 anos) — usando a métrica selecionada da API")

                if len(serie) < 4:
                    st.error("São necessários ao menos 4 anos para ajustar o ETS.")
                else:
                    if st.button("Gerar previsão (5 anos) — API", key="btn_fc_api_5y"):
                        fitted_full = fit_ets(serie["valor"].values)

                        passos = 5
                        fc = np.asarray(fitted_full.forecast(passos), dtype=float)
                        fc = np.maximum(fc, 0.0)

                        anos_fc = np.arange(serie["ano"].max() + 1, serie["ano"].max() + 1 + passos)
                        prev_df = pd.DataFrame({"ano": anos_fc, "previsao": fc})

                        st.dataframe(prev_df, use_container_width=True)

                        hist = serie.rename(columns={"valor": "real"})
                        fig_fc_api = px.line(hist, x="ano", y="real", markers=True,
                                            title=f"Série histórica + Previsão (5 anos) • {col_val}")
                        fig_fc_api.add_scatter(x=prev_df["ano"], y=prev_df["previsao"],
                                            mode="lines+markers", name="Previsão 5 anos")
                        chart(fig_fc_api, key_parts=["previsoes", "api_forecast5", col_val])

                        st.download_button(
                            "📥 Baixar CSV — Previsão 5 anos (API)",
                            prev_df.to_csv(index=False).encode("utf-8"),
                            file_name=f"previsao_5anos_{col_val}.csv",
                            mime="text/csv"
                        )

            # ---------- MODO CSV (igual ao que você curtiu)
            else:
                st.info("CSV com colunas de ano e valor (ex.: `ano`, `valor`).")
                file = st.file_uploader("Selecione o CSV", type=["csv"], key="csv_up_bt")
                if not file:
                    st.stop()

                # leitura tolerante
                try:
                    df = pd.read_csv(file)
                except Exception:
                    df = pd.read_csv(file, sep=";", decimal=",")

                st.write("Prévia do arquivo:")
                st.dataframe(df.head(), use_container_width=True)

                # Helpers de coluna
                def to_year(s: pd.Series) -> pd.Series:
                    if pd.api.types.is_integer_dtype(s):
                        return s.astype(int)
                    p = pd.to_datetime(s, errors="coerce", dayfirst=True)
                    if p.notna().any():
                        return p.dt.year
                    return pd.to_numeric(s, errors="coerce").astype("Int64")

                cand_ano = [c for c in df.columns if "ano" in c.lower() or "year" in c.lower()] or [df.columns[0]]
                col_ano  = st.selectbox("Coluna do ano", df.columns, index=list(df.columns).index(cand_ano[0]))

                num_cols = [c for c in df.columns if c != col_ano and pd.api.types.is_numeric_dtype(df[c])]
                if not num_cols:
                    st.error("Nenhuma coluna numérica além do ano.")
                    st.stop()

                sug = [c for c in num_cols if any(k in c.lower() for k in ["total","valor","produc","import","export"])] or num_cols
                col_val = st.selectbox("Coluna do valor", sug, index=0)

                # Série anual
                serie = df[[col_ano, col_val]].copy()
                serie[col_ano] = to_year(serie[col_ano])
                serie = serie.dropna(subset=[col_ano, col_val])
                serie[col_ano] = serie[col_ano].astype(int)
                serie = serie.groupby(col_ano, as_index=False)[col_val].sum().sort_values(col_ano)
                serie.columns = ["ano", "valor"]

                # ------- Backtest (inalterado: exige ≥ 8 pontos)
                if len(serie) < 8:
                    st.error("Poucos anos. Recomendo ≥ 8 pontos para um backtest confiável.")
                    st.stop()

                anos = serie["ano"].tolist()
                c1, c2 = st.columns(2)
                ini = c1.number_input("Ano inicial do TESTE", min_value=int(anos[1]), max_value=int(anos[-1]), value=int(anos[len(anos)//2]))
                fim = c2.number_input("Ano final do TESTE",   min_value=int(ini),       max_value=int(anos[-1]), value=int(anos[-1]))

                opt_cb, opt_lin = st.columns(2)
                usar_fator = opt_cb.checkbox("Aplicar correção de viés (fator soma real/soma previsto)", value=True)
                usar_linear = opt_lin.checkbox("Aplicar calibração linear a + b·previsto (além do fator)", value=False)

                if st.button("🧪 Rodar Backtest (CSV)", key="run_backtest_csv"):
                    if serie["ano"].min() >= ini:
                        st.error("Precisa existir ao menos UM ano antes do início do teste para treinar o primeiro modelo.")
                        st.stop()

                    back = rolling_backtest(serie, ini, fim)
                    if back.empty:
                        st.error("Nada para testar nesse intervalo (verifique os anos informados).")
                        st.stop()

                    prev = back["previsto_bruto"].values.astype(float)
                    real = back["real"].values.astype(float)

                    fator = (real.sum() / max(prev.sum(), 1e-9)) if usar_fator else 1.0
                    prev_corr = prev * fator

                    calib = None
                    if usar_linear:
                        X = prev_corr.reshape(-1, 1)
                        lr = LinearRegression()
                        lr.fit(X, real)
                        prev_corr = lr.predict(X)
                        calib = (float(lr.intercept_), float(lr.coef_[0]))

                    mae   = mean_absolute_error(real, prev_corr)
                    wape_ = float(np.sum(np.abs(real - prev_corr)) / max(np.sum(np.abs(real)), 1e-9))
                    def _smape(y, yhat):
                        y, yhat = np.asarray(y), np.asarray(yhat)
                        denom = np.abs(y) + np.abs(yhat); denom[denom == 0] = 1e-9
                        return float(np.mean(2 * np.abs(y - yhat) / denom))
                    smap  = _smape(real, prev_corr)

                    out = pd.DataFrame({"ano": back["ano"], "real": real, "previsto": prev_corr})
                    out["erro_abs"] = (out["real"] - out["previsto"]).abs()
                    out["erro_%"]   = (out["real"] - out["previsto"]) / np.where(out["real"]==0, 1e-9, out["real"]) * 100

                    m1, m2, m3 = st.columns(3)
                    m1.metric("MAE", f"{mae:,.0f}")
                    m2.metric("WAPE", f"{wape_*100:,.2f}%")
                    m3.metric("sMAPE", f"{smap*100:,.2f}%")
                    if usar_fator:
                        st.caption(f"Fator de viés aplicado: **{fator:.3f}**")
                    if calib is not None:
                        st.caption(f"Calibração linear: **previsto = {calib[0]:.2f} + {calib[1]:.3f} × previsto_corrigido**")

                    st.subheader("Tabela — Backtest (com correção de viés)")
                    st.dataframe(out, use_container_width=True)

                    fig = px.line(out, x="ano", y="real", markers=True,
                                title=f"Backtest {int(ini)}–{int(fim)} — Real vs Previsto (corrigido)")
                    fig.add_scatter(x=out["ano"], y=out["previsto"], mode="lines+markers", name="Previsto")
                    chart(fig, key_parts=["previsoes", "csv_backtest", ini, fim])

                    st.download_button(
                        "📥 Baixar CSV do backtest",
                        out.to_csv(index=False).encode("utf-8"),
                        file_name=f"backtest_{int(ini)}_{int(fim)}.csv",
                        mime="text/csv"
                    )

                # ------- 🔮 Previsão 5 anos (independente do backtest)
                st.markdown("---")
                st.subheader("🔮 Previsão (5 anos) — usando a coluna selecionada do CSV")

                if len(serie) < 4:
                    st.error("São necessários ao menos 4 anos para ajustar o ETS.")
                else:
                    if st.button("Gerar previsão (5 anos) — CSV", key="btn_fc_csv_5y"):
                        fitted_full = fit_ets(serie["valor"].values)

                        passos = 5
                        fc = np.asarray(fitted_full.forecast(passos), dtype=float)
                        fc = np.maximum(fc, 0.0)

                        anos_fc = np.arange(serie["ano"].max() + 1, serie["ano"].max() + 1 + passos)
                        prev_df = pd.DataFrame({"ano": anos_fc, "previsao": fc})

                        st.dataframe(prev_df, use_container_width=True)

                        hist = serie.rename(columns={"valor": "real"})
                        fig_fc_csv = px.line(hist, x="ano", y="real", markers=True,
                                            title=f"Série histórica + Previsão (5 anos) • {col_val}")
                        fig_fc_csv.add_scatter(x=prev_df["ano"], y=prev_df["previsao"],
                                            mode="lines+markers", name="Previsão 5 anos")
                        chart(fig_fc_csv, key_parts=["previsoes", "csv_forecast5", col_val])

                        st.download_button(
                            "📥 Baixar CSV — Previsão 5 anos (CSV)",
                            prev_df.to_csv(index=False).encode("utf-8"),
                            file_name=f"previsao_5anos_{col_val}.csv",
                            mime="text/csv"
                        )

            st.stop()


        # ===== Demais páginas (dados históricos)
        endpoint = PAGES[page]["endpoint"]
        st.title(f"Dashboard: {page}")

        df = carregar_dados_com_silencio(endpoint)
        if df.empty:
            st.markdown('<div class="empty">Nenhum dado disponível.</div>', unsafe_allow_html=True)
            st.stop()

        produto_col = detectar_coluna_produto(df)
        if produto_col and produto_col in df.columns and pd.api.types.is_string_dtype(df[produto_col]):
            df = df[~df[produto_col].astype(str).str.fullmatch(r"[A-ZÇÃÂÊÁÉÍÓÚÜÑ ]+")]

        busca, anos, produtos = filter_panel(produto_col, df)
        df_filtrado = aplicar_filtros(df.copy(), produto_col, busca, anos, produtos)

        if df_filtrado.empty:
            st.markdown('<div class="empty">Nenhum dado com os filtros atuais. Ajuste os filtros acima.</div>', unsafe_allow_html=True)
            st.stop()

        metricas_disponiveis = [c for c in ["quantidade", "valor"] if c in df_filtrado.columns]
        if not metricas_disponiveis:
            st.warning("Colunas 'quantidade' ou 'valor' não encontradas.")
            st.stop()
        col_metric = st.radio("Visualizar por:", metricas_disponiveis, horizontal=True)

        total = df_filtrado[col_metric].sum()
        anos_series = pd.to_numeric(df_filtrado.get("ano", pd.Series(dtype="float")), errors="coerce").dropna().astype(int)
        yoy_txt = "—"
        if anos_series.nunique() >= 2:
            ys = sorted(anos_series.unique()); y_prev, y_now = ys[-2], ys[-1]
            v_now = df_filtrado.loc[anos_series==y_now, col_metric].sum()
            v_prev= df_filtrado.loc[anos_series==y_prev, col_metric].sum()
            if v_prev != 0:
                rate = (v_now-v_prev)/v_prev
                yoy_txt = f"{'▲' if rate>=0 else '▼'} {abs(rate*100):.1f}%"

        c1, c2, c3, c4 = st.columns(4)
        with c1: metric_card("Total no filtro", human_compact(total))
        with c2: metric_card("Variação YoY", yoy_txt, "Último ano vs. anterior")
        if produto_col and produto_col in df_filtrado.columns:
            s = df_filtrado.groupby(produto_col)[col_metric].sum().sort_values(ascending=False)
            if not s.empty:
                with c3: metric_card("Top produto", s.index[0], f"{human_compact(s.iloc[0])}")
            else:
                with c3: metric_card("Top produto", "—")
        else:
            with c3: metric_card("Top produto", "—")
        with c4: metric_card("Mercados (países)", df_filtrado["pais"].nunique() if "pais" in df_filtrado.columns else "—")

        aba_hist, aba_tabela, aba_grafico_barra, aba_linha, aba_top, aba_comparacao, aba_pareto = st.tabs(
            ["História", "Tabela", "Barra", "Linha", "Top 5", "Comparação", "Pareto"]
        )

        with aba_hist:
            make_story(page, df_filtrado, col_metric, produto_col)

        with aba_tabela:
            st.subheader("Tabela de Dados")
            st.dataframe(df_filtrado, use_container_width=True)
            with st.expander("📥 Exportar dados"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button("CSV", data=df_filtrado.to_csv(index=False),
                                       file_name=f"{endpoint}.csv", mime="text/csv", use_container_width=True)
                with col2:
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
                        df_filtrado.to_excel(writer, index=False, sheet_name="Dados")
                    st.download_button("Excel", data=excel_buffer.getvalue(),
                                       file_name=f"{endpoint}.xlsx",
                                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                       use_container_width=True)
                with col3:
                    st.download_button("JSON",
                                       data=df_filtrado.to_json(orient="records", force_ascii=False),
                                       file_name=f"{endpoint}.json",
                                       mime="application/json", use_container_width=True)

        if "ano" in df_filtrado.columns and col_metric in df_filtrado.columns:
            grafico = (df_filtrado.assign(ano=pd.to_numeric(df_filtrado["ano"], errors="coerce"))
                       .dropna(subset=["ano"])
                       .groupby("ano")[col_metric].sum().reset_index()
                       .sort_values("ano"))
            with aba_grafico_barra:
                fig_bar = px.bar(grafico, x="ano", y=col_metric)
                set_title_and_subtitle(fig_bar, f"{col_metric.title()} por Ano", "Compara volumes/valores por período")
                chart(fig_bar, key_parts=[page, "bar", col_metric])

            with aba_linha:
                fig_linha = px.line(grafico, x="ano", y=col_metric, markers=True)
                last_val = grafico[col_metric].iloc[-1]
                fig_linha.add_hline(y=last_val, line_dash="dot")
                annotate_line_peaks(fig_linha, grafico, "ano", col_metric)
                set_title_and_subtitle(fig_linha, f"Evolução de {col_metric}",
                                       "Linha pontilhada = último ano; anotações de pico/vale")
                chart(fig_linha, key_parts=[page, "line", col_metric])
                

        if produto_col and produto_col in df_filtrado.columns and col_metric in df_filtrado.columns:
            with aba_top:
                top = (df_filtrado.groupby(produto_col)[col_metric].sum()
                       .nlargest(5).reset_index())
                fig_top = px.bar(top, x=produto_col, y=col_metric, text_auto=True)
                set_title_and_subtitle(fig_top, f"Top 5 {produto_col}", "Rápida identificação dos líderes por produto")
                chart(fig_top, key_parts=[page, "top5", col_metric])
                

        with aba_comparacao:
            st.subheader("Comparação entre Períodos")
            if "ano" not in df_filtrado.columns:
                st.warning("A coluna 'ano' não está disponível para comparação.")
            else:
                anos_disp = sorted(pd.to_numeric(df_filtrado["ano"], errors="coerce").dropna().astype(int).unique())
                if len(anos_disp) < 2:
                    st.warning("São necessários pelo menos dois anos distintos para comparar.")
                else:
                    c1c, c2c = st.columns(2)
                    with c1c:
                        periodo1 = st.selectbox("Período 1", anos_disp, index=0, key="comp_ano1")
                    with c2c:
                        idx2 = 1 if len(anos_disp) > 1 else 0
                        periodo2 = st.selectbox("Período 2", anos_disp, index=idx2, key="comp_ano2")

                    if periodo1 == periodo2:
                        st.warning("Selecione dois anos diferentes.")
                    else:
                        anos_int = pd.to_numeric(df_filtrado["ano"], errors="coerce").astype("Int64")
                        df1 = df_filtrado[anos_int==periodo1]
                        df2 = df_filtrado[anos_int==periodo2]

                        col_comp = "quantidade" if "quantidade" in df_filtrado.columns else "valor"
                        if produto_col and produto_col in df_filtrado.columns:
                            g1 = df1.groupby(produto_col)[col_comp].sum().reset_index().rename(columns={col_comp: f"{periodo1}"})
                            g2 = df2.groupby(produto_col)[col_comp].sum().reset_index().rename(columns={col_comp: f"{periodo2}"})
                            comp_df = pd.merge(g1, g2, on=produto_col, how="inner")
                            if comp_df.empty:
                                st.info("Sem interseção de produtos entre os períodos selecionados.")
                            else:
                                comp_df = comp_df.sort_values(by=f"{periodo2}", ascending=False).head(10)
                                fig_comp = px.bar(
                                    comp_df.melt(id_vars=produto_col, var_name="Ano", value_name=col_comp),
                                    x=produto_col, y=col_comp, color="Ano", barmode="group")
                                set_title_and_subtitle(fig_comp,
                                    f"Top 10 Produtos — {periodo1} vs {periodo2}",
                                    "Evidencia ganhos/perdas de participação por produto")
                                chart(fig_comp, key_parts=[page, "comp", col_comp, periodo1, periodo2])
                                

        with aba_pareto:
            group_col = detectar_coluna_produto(df_filtrado) or ("pais" if "pais" in df_filtrado.columns else None)
            if group_col and col_metric in df_filtrado.columns:
                # Série base (ordenada)
                ser = df_filtrado.groupby(group_col)[col_metric].sum().sort_values(ascending=False)

                # ---- monta frame do Pareto
                pf = ser.reset_index()
                pf.columns = ["item", "valor"]
                total = float(pf["valor"].sum())
                if total > 0:
                    pf = pf.assign(
                        share=pf["valor"] / total,
                        rank=range(1, len(pf) + 1)
                    )
                    pf["cum_share"] = pf["share"].cumsum()

                    # ---- helpers locais para rótulo/hover
                    def _truncate(s: str, n: int = 16) -> str:
                        s = str(s)
                        return s if len(s) <= n else s[: max(0, n - 1)] + "…"

                    def _labelize(pf_in: pd.DataFrame, max_chars: int = 16) -> pd.DataFrame:
                        pf_in = pf_in.sort_values("rank").copy()
                        pf_in["label"] = pf_in["item"].astype(str).map(lambda x: _truncate(x, max_chars))
                        pf_in["_item_full"] = pf_in["item"].astype(str)
                        pf_in["_rank"] = pf_in["rank"].astype(int)
                        pf_in["_share_pct"] = (pf_in["share"] * 100).round(1)
                        pf_in["_cum_pct"] = (pf_in["cum_share"] * 100).round(1)
                        return pf_in

                    pf_lab = _labelize(pf, max_chars=16)

                    # ---- gráfico com NOME no eixo X
                    figp = px.line(pf_lab, x="label", y="cum_share", markers=True)
                    figp.update_xaxes(
                        categoryorder="array",
                        categoryarray=pf_lab["label"].tolist(),
                        tickangle=-35
                    )
                    figp.update_xaxes(showticklabels=False, title=None)  # sem rótulos e sem título no eixo
                    figp.update_layout(margin=dict(b=20)) 
                    set_title_and_subtitle(
                        figp,
                        "Curva de Pareto (cobertura cumulativa)",
                        "Linha pontilhada = 80% do total"
                    )
                    figp.add_hline(y=0.8, line_dash="dot")

                    # anotação no ponto de 80%
                    idx80 = pf_lab[pf_lab["cum_share"] >= 0.8]["_rank"].min()
                    if pd.notnull(idx80):
                        label80 = pf_lab.loc[pf_lab["_rank"] == int(idx80), "label"].iloc[0]
                        figp.add_annotation(x=label80, y=0.82, text=f"80% em {int(idx80)} itens", showarrow=False)

                    # hover completo
                    figp.update_traces(
                        customdata=pf_lab[["_item_full", "_rank", "_share_pct", "_cum_pct"]].values,
                        hovertemplate=(
                            "<b>%{customdata[0]}</b><br>"
                            "Rank: %{customdata[1]}<br>"
                            "Share: %{customdata[2]}%<br>"
                            "Acum.: %{customdata[3]}%<br>"
                            "<extra></extra>"
                        )
                    )

                    chart(figp, key_parts=[page, "pareto", group_col, col_metric])
                    
            else:
                st.info("Não há coluna de agrupamento (produto/pais) para construir a Curva de Pareto.")


# Rodapé
st.markdown("<hr/>", unsafe_allow_html=True)
st.caption("Viticultura Dashboard • LOCAL • Docs da API: http://localhost:10000/docs")
