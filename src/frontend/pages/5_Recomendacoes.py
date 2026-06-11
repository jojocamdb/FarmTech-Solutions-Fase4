"""
Pagina: Recomendacoes de Manejo — cruzamento de previsao ML com leituras reais.
"""

import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from src.db.database import get_culturas, get_ultima_leitura, media_cultura
from src.ml.train import carregar_modelo

st.set_page_config(page_title="Recomendacoes — FarmTech", layout="wide")

st.title("Recomendacoes de Manejo")
st.caption("Cruzamento da previsao ML com as ultimas leituras reais dos sensores IoT")

UMIDADE_LIMIAR = 60.0
PH_FAIXAS: dict[str, tuple[float, float]] = {
    "rice": (6.0, 7.0),
    "maize": (5.8, 7.0),
    "chickpea": (6.0, 7.5),
    "kidneybeans": (6.0, 7.5),
    "pigeonpeas": (5.5, 7.0),
    "mothbeans": (6.0, 7.5),
    "mungbean": (6.0, 7.5),
    "blackgram": (6.0, 7.0),
    "lentil": (6.0, 7.0),
    "pomegranate": (5.5, 7.5),
    "banana": (5.5, 7.0),
    "mango": (5.5, 7.5),
    "grapes": (5.5, 6.5),
    "watermelon": (6.0, 7.0),
    "muskmelon": (6.0, 7.5),
    "apple": (5.5, 6.5),
    "orange": (6.0, 7.5),
    "papaya": (6.0, 7.0),
    "coconut": (5.0, 8.0),
    "cotton": (6.0, 8.0),
    "jute": (6.0, 7.0),
    "coffee": (6.0, 6.5),
}
PH_PADRAO = (6.0, 7.0)

# ── Dados ────────────────────────────────────────────────────────────────────
try:
    culturas = get_culturas()
    ultima = get_ultima_leitura()
except Exception as e:
    st.error(f"Erro ao acessar banco: {e}")
    st.stop()

if not culturas:
    st.warning("Banco nao inicializado. Execute scripts/init_db.py.")
    st.stop()

modelo_rainfall = carregar_modelo("rainfall")
modelo_humidity = carregar_modelo("humidity")
if not modelo_rainfall or not modelo_humidity:
    st.warning("Modelos nao treinados. Acesse Pipeline ML e clique em 'Retreinar modelos'.")
    st.stop()

if not ultima:
    st.warning("Nenhuma leitura de sensor disponivel.")
    st.stop()

# ── Formulario ────────────────────────────────────────────────────────────────
st.markdown("### Selecione a Cultura e Parametros de Previsao")

with st.form("form_recom"):
    col1, col2 = st.columns(2)
    with col1:
        cultura = st.selectbox("Cultura", culturas)
        n = st.slider("N (kg/ha)", 0, 140, int(ultima.get("n", 0)) * 40 + 40)
        p = st.slider("P (kg/ha)", 5, 145, int(ultima.get("p", 0)) * 40 + 30)
    with col2:
        k = st.slider("K (kg/ha)", 5, 205, int(ultima.get("k", 0)) * 40 + 20)
        temperatura = st.slider("Temperatura (C)", 5.0, 50.0, float(ultima.get("temp_c", 25.0)), step=0.5)
        ph_entrada = st.slider("pH do solo", 3.5, 10.0, float(ultima.get("ph", 6.5)), step=0.1)

    analisar = st.form_submit_button("Gerar Recomendacoes")

if not analisar:
    st.info("Preencha os parametros e clique em 'Gerar Recomendacoes'.")
    st.stop()

# ── Previsao ─────────────────────────────────────────────────────────────────
entrada = pd.DataFrame([{
    "n": n, "p": p, "k": k,
    "temperatura": temperatura, "ph": ph_entrada,
    "cultura": cultura,
}])

try:
    prev_rainfall = max(0.0, float(modelo_rainfall.predict(entrada)[0]))
    prev_humidity = max(0.0, min(100.0, float(modelo_humidity.predict(entrada)[0])))
except Exception as e:
    st.error(f"Erro na previsao: {e}")
    st.stop()

st.markdown("---")
st.markdown("### Leituras Reais vs Previsao")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Umidade sensor (%)", f"{ultima['umidade']:.1f}")
c2.metric("Necessidade hidrica prevista", f"{prev_rainfall:.1f} mm")
c3.metric("pH sensor", f"{ultima['ph']:.3f}")
c4.metric("Umidade esperada pela cultura", f"{prev_humidity:.1f} %")

# ── Recomendacoes ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Recomendacoes de Manejo")

recomendacoes: list[dict] = []

# 1. Bomba de irrigacao
umid_sensor = float(ultima["umidade"])
if prev_rainfall > 150 and umid_sensor < UMIDADE_LIMIAR:
    deficit = UMIDADE_LIMIAR - umid_sensor
    tempo_est = round(deficit * 0.5, 1)
    recomendacoes.append({
        "tipo": "error",
        "titulo": "Acionamento da Bomba Recomendado",
        "texto": (
            f"A necessidade hidrica prevista e alta ({prev_rainfall:.1f} mm) e a umidade "
            f"atual do sensor ({umid_sensor:.1f}%) esta abaixo do limiar ({UMIDADE_LIMIAR}%). "
            f"Deficit de umidade: {deficit:.1f}%. "
            f"Tempo estimado de irrigacao: {tempo_est} minutos."
        ),
    })
elif umid_sensor < UMIDADE_LIMIAR:
    deficit = UMIDADE_LIMIAR - umid_sensor
    recomendacoes.append({
        "tipo": "warning",
        "titulo": "Umidade Abaixo do Limiar",
        "texto": (
            f"Umidade do sensor: {umid_sensor:.1f}% (limiar: {UMIDADE_LIMIAR}%). "
            f"Deficit: {deficit:.1f}%. Considere irrigacao suplementar."
        ),
    })
else:
    recomendacoes.append({
        "tipo": "success",
        "titulo": "Umidade Adequada",
        "texto": (
            f"Umidade do sensor ({umid_sensor:.1f}%) acima do limiar ({UMIDADE_LIMIAR}%). "
            "Irrigacao nao necessaria no momento."
        ),
    })

# 2. NPK — comparar com media da cultura
medias = media_cultura(cultura)
if medias:
    n_med = medias["n_med"] or 0
    p_med = medias["p_med"] or 0
    k_med = medias["k_med"] or 0
    tol = 0.25  # ± 25% de tolerancia

    ajustes = []
    if n and abs(n - n_med) / (n_med + 1) > tol:
        direcao = "aumentar" if n < n_med else "reduzir"
        ajustes.append(f"N: {n:.0f} kg/ha (media da cultura: {n_med:.0f} kg/ha) — {direcao} aplicacao")
    if p and abs(p - p_med) / (p_med + 1) > tol:
        direcao = "aumentar" if p < p_med else "reduzir"
        ajustes.append(f"P: {p:.0f} kg/ha (media da cultura: {p_med:.0f} kg/ha) — {direcao} aplicacao")
    if k and abs(k - k_med) / (k_med + 1) > tol:
        direcao = "aumentar" if k < k_med else "reduzir"
        ajustes.append(f"K: {k:.0f} kg/ha (media da cultura: {k_med:.0f} kg/ha) — {direcao} aplicacao")

    if ajustes:
        recomendacoes.append({
            "tipo": "warning",
            "titulo": "Ajuste de Macronutrientes Recomendado",
            "texto": "Comparando com a media historica da cultura selecionada:\n\n" + "\n\n".join(f"- {a}" for a in ajustes),
        })
    else:
        recomendacoes.append({
            "tipo": "success",
            "titulo": "Macronutrientes Adequados",
            "texto": f"N, P e K estao dentro da faixa esperada para {cultura} (± 25% da media historica).",
        })

# 3. Correcao de pH
ph_sensor = float(ultima["ph"])
ph_min, ph_max = PH_FAIXAS.get(cultura.lower(), PH_PADRAO)

if ph_sensor < ph_min:
    recomendacoes.append({
        "tipo": "warning",
        "titulo": "pH Abaixo da Faixa Ideal",
        "texto": (
            f"pH sensor: {ph_sensor:.3f} | Faixa ideal para {cultura}: {ph_min}–{ph_max}. "
            f"Deficit: {ph_min - ph_sensor:.3f} unidades. "
            "Recomenda-se calagem (calcario dolomitico) para elevar o pH."
        ),
    })
elif ph_sensor > ph_max:
    recomendacoes.append({
        "tipo": "warning",
        "titulo": "pH Acima da Faixa Ideal",
        "texto": (
            f"pH sensor: {ph_sensor:.3f} | Faixa ideal para {cultura}: {ph_min}–{ph_max}. "
            f"Excesso: {ph_sensor - ph_max:.3f} unidades. "
            "Recomenda-se aplicacao de enxofre agricola ou materia organica para reduzir o pH."
        ),
    })
else:
    recomendacoes.append({
        "tipo": "success",
        "titulo": "pH Adequado",
        "texto": (
            f"pH sensor ({ph_sensor:.3f}) dentro da faixa ideal para {cultura} ({ph_min}–{ph_max})."
        ),
    })

# Exibir recomendacoes
for rec in recomendacoes:
    if rec["tipo"] == "error":
        st.error(f"**{rec['titulo']}**\n\n{rec['texto']}")
    elif rec["tipo"] == "warning":
        st.warning(f"**{rec['titulo']}**\n\n{rec['texto']}")
    else:
        st.success(f"**{rec['titulo']}**\n\n{rec['texto']}")
