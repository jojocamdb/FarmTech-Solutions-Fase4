"""
Pagina: Analise Exploratoria — dataset agronômico.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
import numpy as np
import streamlit as st

from src.db.database import get_amostras_agronomicas

st.set_page_config(page_title="Analise Exploratoria — FarmTech", layout="wide")

st.title("Analise Exploratoria")
st.caption("Dataset Atividade Cap10 — 2.200 amostras, 22 culturas")

# ── Carregar dados ───────────────────────────────────────────────────────────
try:
    amostras = get_amostras_agronomicas()
except Exception as e:
    st.error(f"Erro ao acessar banco: {e}")
    st.stop()

if not amostras:
    st.warning("Nenhuma amostra disponivel. Execute scripts/init_db.py primeiro.")
    st.stop()

df = pd.DataFrame(amostras)
COLUNAS_NUM = ["n", "p", "k", "temperatura", "umidade", "ph", "chuva"]

# ── Filtros ──────────────────────────────────────────────────────────────────
culturas_disp = sorted(df["cultura"].unique())
culturas_sel = st.multiselect(
    "Filtrar por cultura (vazio = todas)",
    culturas_disp,
    default=[],
)
df_filt = df[df["cultura"].isin(culturas_sel)] if culturas_sel else df.copy()

st.caption(f"{len(df_filt):,} amostras selecionadas de {df_filt['cultura'].nunique()} culturas")

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Heatmap de Correlacao",
    "Distribuicoes por Cultura",
    "Boxplots",
    "Scatter entre Variaveis",
    "Estatisticas Descritivas",
])

with tab1:
    st.markdown("#### Heatmap de Correlacao (variaveis numericas)")
    corr = df_filt[COLUNAS_NUM].corr()
    fig = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1,
        title="Correlacao de Pearson",
    )
    fig.update_layout(width=700, height=600)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    var = st.selectbox("Variavel", COLUNAS_NUM, key="dist_var")
    top_n = st.slider("Numero de culturas", 3, 22, 10, key="dist_top")
    culturas_top = df_filt.groupby("cultura")[var].mean().nlargest(top_n).index.tolist()
    df_top = df_filt[df_filt["cultura"].isin(culturas_top)]

    fig = px.histogram(
        df_top,
        x=var,
        color="cultura",
        barmode="overlay",
        opacity=0.7,
        nbins=40,
        title=f"Distribuicao de {var} por cultura (top {top_n} por media)",
        labels={var: var, "count": "frequencia"},
    )
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    var_box = st.selectbox("Variavel", COLUNAS_NUM, key="box_var")
    n_cult = st.slider("Numero de culturas", 3, 22, 12, key="box_n")
    culturas_box = df_filt.groupby("cultura")[var_box].median().nlargest(n_cult).index.tolist()
    df_box = df_filt[df_filt["cultura"].isin(culturas_box)]

    fig = px.box(
        df_box,
        x="cultura",
        y=var_box,
        color="cultura",
        title=f"Boxplot de {var_box} por cultura",
    )
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    c1, c2 = st.columns(2)
    with c1:
        eixo_x = st.selectbox("Eixo X", COLUNAS_NUM, index=0, key="sc_x")
    with c2:
        eixo_y = st.selectbox("Eixo Y", COLUNAS_NUM, index=6, key="sc_y")
    amostra_sc = df_filt.sample(min(len(df_filt), 500), random_state=42)
    fig = px.scatter(
        amostra_sc,
        x=eixo_x,
        y=eixo_y,
        color="cultura",
        opacity=0.7,
        title=f"{eixo_x} vs {eixo_y} (amostra de 500 pontos)",
    )
    st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.dataframe(
        df_filt[COLUNAS_NUM + ["cultura"]].describe().T.round(2),
        use_container_width=True,
    )
    st.markdown("#### Contagem por Cultura")
    contagem = df_filt["cultura"].value_counts().reset_index()
    contagem.columns = ["cultura", "amostras"]
    fig_bar = px.bar(
        contagem,
        x="cultura",
        y="amostras",
        color="amostras",
        color_continuous_scale="Tealgrn",
        title="Amostras por cultura",
    )
    fig_bar.update_xaxes(tickangle=45)
    st.plotly_chart(fig_bar, use_container_width=True)
