"""
Pagina: Sensores IoT — leituras registradas do prototipo ESP32/Wokwi.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st

from src.db.database import get_leituras, get_ultima_leitura

st.set_page_config(page_title="Sensores IoT — FarmTech", layout="wide")

st.title("Sensores IoT")
st.caption("Leituras registradas/simuladas do prototipo ESP32/Wokwi, armazenadas pelo scheduler")

# ── Botao de atualizar ───────────────────────────────────────────────────────
col_btn, col_status = st.columns([1, 4])
with col_btn:
    if st.button("Atualizar leituras"):
        st.rerun()

with col_status:
    sched = st.session_state.get("scheduler_holder", {})
    if sched.get("scheduler"):
        st.success("Scheduler ativo — registrando leituras simuladas a cada 30s")
    elif sched.get("erro"):
        st.warning(f"Scheduler inativo: {sched['erro']}")
    else:
        st.info("Scheduler nao iniciado ainda.")

# ── Dados ────────────────────────────────────────────────────────────────────
try:
    leituras = get_leituras(limite=200)
    ultima = get_ultima_leitura()
except Exception as e:
    st.error(f"Erro ao acessar banco: {e}")
    st.stop()

if not leituras:
    st.warning("Nenhuma leitura registrada disponivel. Execute scripts/init_db.py primeiro.")
    st.stop()

df = pd.DataFrame(leituras)
df["ts"] = pd.to_datetime(df["ts"], format="mixed")
df = df.sort_values("ts")

# ── Indicadores da ultima leitura ────────────────────────────────────────────
st.markdown("### Ultima Leitura Registrada")
if ultima:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Umidade (%)", f"{ultima['umidade']:.1f}")
    c2.metric("Temperatura (C)", f"{ultima['temp_c']:.1f}")
    c3.metric("pH", f"{ultima['ph']:.3f}")
    c4.metric("LDR", f"{int(ultima['ldr'])}")
    bomba_label = "LIGADA" if ultima["bomba_fw"] == 1 else "DESLIGADA"
    c5.metric("Bomba", bomba_label)

# ── Series temporais ─────────────────────────────────────────────────────────
st.markdown("### Series de Leituras Registradas")

tab1, tab2, tab3, tab4 = st.tabs(["Umidade", "Temperatura", "pH", "Estado da Bomba"])

with tab1:
    fig = px.line(df, x="ts", y="umidade", title="Umidade registrada ao longo do tempo (%)",
                  labels={"ts": "Timestamp", "umidade": "Umidade (%)"})
    fig.add_hline(y=60, line_dash="dash", line_color="orange",
                  annotation_text="Limiar irrigacao (60%)")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    fig = px.line(df, x="ts", y="temp_c", title="Temperatura registrada ao longo do tempo (C)",
                  labels={"ts": "Timestamp", "temp_c": "Temperatura (C)"},
                  color_discrete_sequence=["#EF553B"])
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    fig = px.line(df, x="ts", y="ph", title="pH registrado ao longo do tempo",
                  labels={"ts": "Timestamp", "ph": "pH"},
                  color_discrete_sequence=["#00CC96"])
    fig.add_hrect(y0=6.0, y1=7.5, fillcolor="green", opacity=0.08,
                  annotation_text="Faixa de referencia (6-7.5)")
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    fig = px.scatter(df, x="ts", y="bomba_fw", title="Estado registrado da Bomba (1=LIGADA)",
                     labels={"ts": "Timestamp", "bomba_fw": "Bomba"},
                     color="bomba_fw",
                     color_continuous_scale=["#1F77B4", "#FF7F0E"])
    fig.update_yaxes(tickvals=[0, 1], ticktext=["DESLIGADA", "LIGADA"])
    st.plotly_chart(fig, use_container_width=True)

# ── Tabela de ultimas leituras ────────────────────────────────────────────────
st.markdown("### Ultimas Leituras Registradas")
df_display = df.sort_values("ts", ascending=False).head(30).copy()
df_display["bomba_fw"] = df_display["bomba_fw"].map({1: "LIGADA", 0: "DESLIGADA"})
df_display["ts"] = df_display["ts"].dt.strftime("%Y-%m-%d %H:%M:%S")
st.dataframe(
    df_display[["ts", "umidade", "temp_c", "ph", "ldr", "n", "p", "k", "bomba_fw"]],
    use_container_width=True,
    hide_index=True,
)

# ── NPK atual ────────────────────────────────────────────────────────────────
if ultima:
    st.markdown("### Nutrientes (ultima leitura registrada)")
    cn, cp, ck = st.columns(3)
    cn.metric("Nitrogenio (N)", "Presente" if ultima["n"] else "Ausente")
    cp.metric("Fosforo (P)", "Presente" if ultima["p"] else "Ausente")
    ck.metric("Potassio (K)", "Presente" if ultima["k"] else "Ausente")
