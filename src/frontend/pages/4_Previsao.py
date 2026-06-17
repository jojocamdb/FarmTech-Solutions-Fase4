"""
Pagina: Previsao Agricola — formulario com cultura e NPK/temp/pH.
"""

import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from src.db.database import get_culturas, inserir_previsao
from src.ml.train import carregar_modelo, carregar_metricas

st.set_page_config(page_title="Previsao — FarmTech", layout="wide")

st.title("Previsao Agricola")
st.caption("Estime o proxy de necessidade hidrica (rainfall) e a umidade esperada (humidity) para uma cultura")

# ── Carregar culturas ─────────────────────────────────────────────────────────
try:
    culturas = get_culturas()
except Exception as e:
    st.error(f"Erro ao acessar banco: {e}")
    st.stop()

if not culturas:
    st.warning("Banco nao inicializado. Execute scripts/init_db.py.")
    st.stop()

# ── Verificar modelos ────────────────────────────────────────────────────────
modelo_rainfall = carregar_modelo("rainfall")
modelo_humidity = carregar_modelo("humidity")

if not modelo_rainfall or not modelo_humidity:
    st.warning("Modelos nao treinados. Va para Pipeline ML e clique em 'Retreinar modelos'.")
    st.stop()

metricas = carregar_metricas() or {}

# ── Formulario de previsao ────────────────────────────────────────────────────
st.markdown("### Parametros de Entrada")

with st.form("form_previsao"):
    col1, col2 = st.columns(2)

    with col1:
        cultura = st.selectbox("Cultura", culturas)
        n = st.slider("Nitrogenio — N (kg/ha)", min_value=0, max_value=140, value=60)
        p = st.slider("Fosforo — P (kg/ha)", min_value=5, max_value=145, value=55)

    with col2:
        k = st.slider("Potassio — K (kg/ha)", min_value=5, max_value=205, value=44)
        temperatura = st.slider("Temperatura (C)", min_value=5.0, max_value=50.0, value=25.0, step=0.5)
        ph = st.slider("pH do solo", min_value=3.5, max_value=10.0, value=6.5, step=0.1)

    submeter = st.form_submit_button("Prever")

# ── Resultado da previsao ─────────────────────────────────────────────────────
if submeter:
    entrada = pd.DataFrame([{
        "n": n,
        "p": p,
        "k": k,
        "temperatura": temperatura,
        "ph": ph,
        "cultura": cultura,
    }])

    try:
        prev_rainfall = float(modelo_rainfall.predict(entrada)[0])
        prev_humidity = float(modelo_humidity.predict(entrada)[0])

        # Clipping para faixas plausíveis
        prev_rainfall = max(0.0, prev_rainfall)
        prev_humidity = max(0.0, min(100.0, prev_humidity))

        st.markdown("---")
        st.markdown("### Resultado do Modelo Treinado")

        c1, c2 = st.columns(2)
        with c1:
            st.metric(
                label="Proxy de Necessidade Hidrica (rainfall)",
                value=f"{prev_rainfall:.2f} mm",
                help="Valor previsto para rainfall, usado como proxy de necessidade hidrica. Nao deve ser interpretado como volume direto de irrigacao.",
            )
            met_r = metricas.get("rainfall", {})
            if met_r:
                melhor_r = met_r.get("melhor_modelo", "?")
                r2_r = next((m["r2"] for m in met_r.get("metricas", []) if m["modelo"] == melhor_r), None)
                st.caption(f"Modelo: {melhor_r} | R² no teste: {r2_r:.4f}" if r2_r else f"Modelo: {melhor_r}")

        with c2:
            st.metric(
                label="Umidade Esperada do Ambiente",
                value=f"{prev_humidity:.2f} %",
                help="Umidade ambiental esperada para esta cultura nessas condicoes.",
            )
            met_h = metricas.get("humidity", {})
            if met_h:
                melhor_h = met_h.get("melhor_modelo", "?")
                r2_h = next((m["r2"] for m in met_h.get("metricas", []) if m["modelo"] == melhor_h), None)
                st.caption(f"Modelo: {melhor_h} | R² no teste: {r2_h:.4f}" if r2_h else f"Modelo: {melhor_h}")

        # Interpretacao da necessidade hidrica
        if prev_rainfall > 150:
            st.warning("Proxy indica alta necessidade hidrica; avalie o manejo de irrigacao com dados agronomicos complementares.")
        elif prev_rainfall > 80:
            st.info("Proxy indica necessidade hidrica moderada.")
        else:
            st.success("Proxy indica baixa necessidade hidrica no cenario informado.")

        # Gravar na tabela previsoes
        params = json.dumps({
            "cultura": cultura, "n": n, "p": p, "k": k,
            "temperatura": temperatura, "ph": ph,
        }, ensure_ascii=False)
        nome_modelo_r = metricas.get("rainfall", {}).get("melhor_modelo", "modelo_rainfall")
        nome_modelo_h = metricas.get("humidity", {}).get("melhor_modelo", "modelo_humidity")

        inserir_previsao(nome_modelo_r, "rainfall", prev_rainfall, params)
        inserir_previsao(nome_modelo_h, "humidity", prev_humidity, params)

        st.caption("Previsao registrada na tabela previsoes do banco de dados.")

    except Exception as e:
        st.error(f"Erro na previsao: {e}")

# ── Informacoes dos modelos ────────────────────────────────────────────────────
with st.expander("Informacoes sobre os modelos utilizados"):
    st.markdown(
        """
**Premissas importantes:**

- `rainfall` e usado como **proxy de necessidade hidrica** da cultura, nao como volume direto
  de irrigacao. O dataset agronômico usa chuva como variavel de condicao de cultivo.
- `humidity` representa a **umidade ambiental esperada** para a cultura nas condicoes fornecidas.
- Features: N, P, K, temperatura, pH e cultura (one-hot encoding).
- Modelos comparados: LinearRegression, Ridge (GridSearchCV), RandomForestRegressor.
- Split treino/teste: 80/20 com random_state=42.
- Validacao cruzada k-fold (k=5) para R².
        """
    )
