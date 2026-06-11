"""
FarmTech Solutions — Assistente Agrícola Inteligente.
Aplicação principal Streamlit (ponto de entrada).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st

st.set_page_config(
    page_title="FarmTech Solutions",
    page_icon="assets/logo_fiap.webp",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inicia o scheduler de simulação IoT uma única vez por sessão
if "scheduler_holder" not in st.session_state:
    st.session_state["scheduler_holder"] = {}

try:
    from src.frontend.scheduler import iniciar_scheduler
    iniciar_scheduler(st.session_state["scheduler_holder"])
except Exception as e:
    st.session_state["scheduler_holder"]["erro"] = str(e)

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    try:
        st.image("assets/logo_fiap.webp", width=120)
    except Exception:
        st.markdown("**FIAP**")
    st.markdown("---")
    st.markdown("### FarmTech Solutions")
    st.caption("Assistente Agricola Inteligente")
    st.markdown("---")
    st.caption("Fase 4 — Projeto FarmTech")
    st.caption("Grupo 47")

# ── Home ────────────────────────────────────────────────────────────────────
st.title("FarmTech Solutions")
st.subheader("Assistente Agricola Inteligente — Visao Geral")

st.markdown(
    """
    Plataforma de monitoramento e analise para o agronegocio, integrando dados de
    sensores IoT (ESP32 simulado no Wokwi) com Machine Learning supervisionado
    para recomendacoes de irrigacao e manejo de culturas.
    """
)

col1, col2 = st.columns([3, 2])

with col1:
    st.markdown("#### Arquitetura do Sistema")
    st.code(
        """
┌─────────────────────────────────────────────┐
│              FarmTech Solutions             │
├─────────────────────────────────────────────┤
│  ESP32 (Wokwi)  →  CSV histórico            │
│       ↓                                     │
│  SQLite (farmtech.db)                       │
│  ├── culturas                               │
│  ├── sensores                               │
│  ├── leituras_sensores  ← APScheduler       │
│  ├── amostras_agronomicas                   │
│  └── previsoes                              │
│       ↓                                     │
│  Scikit-Learn Pipeline                      │
│  ├── LinearRegression (baseline)            │
│  ├── Ridge (GridSearchCV)                   │
│  └── RandomForestRegressor                  │
│       ↓                                     │
│  Dashboard Streamlit (7 páginas)            │
└─────────────────────────────────────────────┘
        """,
        language="text",
    )

with col2:
    st.markdown("#### Status do Banco de Dados")
    try:
        from src.db.database import status_banco

        status = status_banco()
        for tabela, total in status.items():
            st.metric(tabela, f"{total:,} registros")
    except Exception as e:
        st.warning(f"Banco nao inicializado. Execute: python scripts/init_db.py\n\n{e}")

st.markdown("---")
st.markdown("#### Paginas Disponíveis")

cols = st.columns(3)
paginas = [
    ("Sensores IoT", "Monitoramento em tempo quase real das leituras do ESP32 com scheduler ativo."),
    ("Analise Exploratoria", "Heatmaps, distribuicoes por cultura, boxplots e scatter entre variaveis."),
    ("Pipeline ML", "Comparacao de modelos, metricas, residuos e feature importance."),
    ("Previsao em Tempo Real", "Formulario de previsao de necessidade hidrica e umidade esperada."),
    ("Recomendacoes de Manejo", "Regras agronomicas cruzando previsao ML com leituras reais dos sensores."),
    ("Historico de Previsoes", "Consulta ao historico de todas as previsoes realizadas."),
]
for i, (titulo, descricao) in enumerate(paginas):
    with cols[i % 3]:
        st.info(f"**{titulo}**\n\n{descricao}")

st.markdown("---")
st.caption(
    "FIAP — Fase 4 | Grupo: Jocasta Bortolacci, Marina Soares, Carlos Amaral, Georgia Rocha, Edemir Sufiatti | "
    "Tutor: Nicolly Candida | Coordenador: Andre Godoi Chiovato"
)
