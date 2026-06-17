"""
Pagina: Pipeline ML — comparacao de modelos, metricas, residuos, feature importance.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

MODELS_DIR = ROOT / "src" / "ml" / "models"

st.set_page_config(page_title="Pipeline ML — FarmTech", layout="wide")

st.title("Pipeline de Machine Learning")
st.caption("Regressao supervisionada — targets: rainfall (necessidade hidrica) e humidity (umidade esperada)")

# ── Treinar / carregar ────────────────────────────────────────────────────────
col_btn, col_info = st.columns([1, 4])
with col_btn:
    retreinar = st.button("Retreinar modelos")

if retreinar:
    with st.spinner("Treinando modelos... (pode levar alguns segundos)"):
        try:
            from src.ml.train import treinar
            resultados = treinar(verbose=False)
            st.success("Modelos retreinados com sucesso.")
            st.session_state["ml_retreinado"] = True
        except Exception as e:
            st.error(f"Erro no treinamento: {e}")
            st.stop()

# ── Carregar metricas salvas ─────────────────────────────────────────────────
metricas_path = MODELS_DIR / "metricas.json"
if not metricas_path.exists():
    st.info("Modelos ainda nao treinados. Clique em 'Retreinar modelos' ou execute: python src/ml/train.py")
    st.stop()

with open(metricas_path) as f:
    resultados = json.load(f)

# ── Tabs por target ───────────────────────────────────────────────────────────
targets = list(resultados.keys())
tabs = st.tabs([f"Target: {t}" for t in targets] + ["Feature Importance"])

for i, target in enumerate(targets):
    with tabs[i]:
        info = resultados[target]
        melhor = info["melhor_modelo"]
        metricas_lista = info["metricas"]

        st.markdown(f"**Modelo selecionado pelo maior R2 no teste:** `{melhor}`")

        # Tabela comparativa
        st.markdown("#### Tabela Comparativa de Modelos")
        df_met = pd.DataFrame(metricas_lista)
        df_met = df_met.rename(columns={
            "modelo": "Modelo",
            "mae": "MAE",
            "mse": "MSE",
            "rmse": "RMSE",
            "r2": "R²",
            "cv_r2_media": "CV R² (media)",
            "cv_r2_desvio": "CV R² (desvio)",
        })
        # Destaca melhor linha
        def destacar(row):
            if row["Modelo"] == melhor:
                return ["background-color: #1A3A1A"] * len(row)
            return [""] * len(row)
        st.dataframe(
            df_met.style.apply(destacar, axis=1).format({
                "MAE": "{:.4f}", "MSE": "{:.4f}", "RMSE": "{:.4f}",
                "R²": "{:.4f}", "CV R² (media)": "{:.4f}", "CV R² (desvio)": "{:.4f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

        # Graficos de barras de R²
        fig_r2 = px.bar(
            df_met,
            x="Modelo",
            y="R²",
            color="R²",
            color_continuous_scale="Greens",
            title=f"R² por modelo — target: {target}",
            text_auto=".4f",
        )
        fig_r2.update_layout(showlegend=False)
        st.plotly_chart(fig_r2, use_container_width=True)

        # Analise de residuos
        residuos_path = MODELS_DIR / f"residuos_{target}.csv"
        if residuos_path.exists():
            st.markdown("#### Analise de Residuos (melhor modelo)")
            df_res = pd.read_csv(residuos_path)

            c1, c2 = st.columns(2)
            with c1:
                fig_rv = px.scatter(
                    df_res,
                    x="y_previsto",
                    y="residuo",
                    title="Residuo vs Previsto",
                    labels={"y_previsto": "Valor Previsto", "residuo": "Residuo"},
                    opacity=0.6,
                )
                fig_rv.add_hline(y=0, line_dash="dash", line_color="red")
                st.plotly_chart(fig_rv, use_container_width=True)

            with c2:
                fig_hist = px.histogram(
                    df_res,
                    x="residuo",
                    nbins=40,
                    title="Histograma de Residuos",
                    labels={"residuo": "Residuo", "count": "Frequencia"},
                    color_discrete_sequence=["#E8175D"],
                )
                st.plotly_chart(fig_hist, use_container_width=True)

            # Grafico previsto vs real
            fig_pv = px.scatter(
                df_res,
                x="y_real",
                y="y_previsto",
                title="Previsto vs Real",
                labels={"y_real": "Valor Real", "y_previsto": "Valor Previsto"},
                opacity=0.6,
            )
            # Linha de identidade
            mn = float(min(df_res["y_real"].min(), df_res["y_previsto"].min()))
            mx = float(max(df_res["y_real"].max(), df_res["y_previsto"].max()))
            fig_pv.add_trace(go.Scatter(
                x=[mn, mx], y=[mn, mx],
                mode="lines", name="Ideal",
                line=dict(color="red", dash="dash"),
            ))
            st.plotly_chart(fig_pv, use_container_width=True)

# ── Feature Importance ────────────────────────────────────────────────────────
with tabs[len(targets)]:
    st.markdown("#### Feature Importance — Random Forest")
    for target in targets:
        imp_path = MODELS_DIR / f"importancias_{target}.csv"
        if imp_path.exists():
            df_imp = pd.read_csv(imp_path).head(15)
            fig = px.bar(
                df_imp,
                x="importance",
                y="feature",
                orientation="h",
                title=f"Feature Importance — target: {target}",
                labels={"importance": "Importancia", "feature": "Variavel"},
                color="importance",
                color_continuous_scale="Teal",
            )
            fig.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"Importancias do target {target} nao disponiveis (modelo pode nao ser RandomForest).")
