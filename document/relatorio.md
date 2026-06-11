# Relatório Técnico — FarmTech Solutions
## Fase 4 — Assistente Agrícola Inteligente

**FIAP — Pós-Graduação em Inteligência Artificial para Devs**
Grupo 47 | Junho de 2026

---

## 1. Modelagem do Banco de Dados

### Estrutura relacional

O banco SQLite (`farmtech.db`) é composto por cinco tabelas normalizadas:

- **culturas** — catálogo de 22 culturas do dataset agronômico.
- **sensores** — cadastro de sensores IoT; permite registrar múltiplos dispositivos.
- **leituras_sensores** — 153 leituras históricas do ESP32 (Wokwi) + leituras simuladas pelo APScheduler.
- **amostras_agronomicas** — 2.200 amostras do dataset Cap10, vinculadas às culturas.
- **previsoes** — histórico de todas as previsões realizadas via interface.

A separação em tabelas distintas evita redundância e garante integridade referencial via chaves estrangeiras
(`PRAGMA foreign_keys = ON`). Todas as queries são parametrizadas — nunca há interpolação direta de variáveis
em SQL.

### Script de inicialização

`scripts/init_db.py` lê os dois CSVs, cria o schema e popula o banco em uma única execução. A linha de
separação `===` presente no CSV de irrigação é ignorada via verificação explícita no parser.

---

## 2. Premissas dos Targets de ML

### rainfall — proxy de necessidade hídrica

**Importante:** `rainfall` (chuva em mm) **não é uma medição direta de rendimento**. No dataset agronômico
Cap10, essa coluna representa a precipitação pluviométrica histórica associada às condições de cultivo
favoráveis à cultura. Usamos `rainfall` como **proxy de necessidade hídrica** — culturas com alta rainfall
histórica geralmente demandam mais água para se desenvolver adequadamente.

Essa é uma interpretação prática, não uma relação causal direta. A recomendação de irrigação deve ser
complementada com a leitura real dos sensores (umidade, temperatura) e com o conhecimento agronômico local.

### humidity — umidade ambiental esperada

`humidity` representa a umidade relativa do ar esperada para que a cultura prospere nas condições fornecidas
(N, P, K, temperatura, pH). É usada para comparar com a umidade medida pelos sensores e sugerir
ajustes microclimáticos (ventilação, cobertura, irrigação por aspersão).

---

## 3. Metodologia de Machine Learning

### Pipeline Scikit-Learn

Cada target (`rainfall`, `humidity`) tem seu próprio pipeline independente:

```
ColumnTransformer
├── passthrough   → N, P, K, temperatura, pH
└── OneHotEncoder → cultura (22 categorias)
         ↓
    Estimador
```

### Modelos comparados

| Modelo | Tipo | Hiperparâmetros |
|---|---|---|
| LinearRegression | Baseline | — |
| Ridge | Regularização L2 | alpha: [0.1, 1, 10, 100] via GridSearchCV |
| RandomForestRegressor | Ensemble | n_estimators=100, random_state=42 |

### Protocolo de avaliação

- **Split treino/teste:** 80/20, `random_state=42` fixo para reprodutibilidade.
- **Validação cruzada:** K-Fold, k=5, métrica R². Reporta média ± desvio padrão.
- **Métricas no teste:** MAE, MSE, RMSE, R².
- **Análise de resíduos:** gráfico resíduo vs previsto + histograma de resíduos.
- **Feature importance:** Random Forest, top 15 features exibidas no dashboard.

### Persistência

Os melhores pipelines são salvos em `src/ml/models/modelo_<target>.joblib`. As métricas são salvas em
`src/ml/models/metricas.json` para consumo pelo dashboard sem re-executar o treinamento.

---

## 4. Interpretação das Métricas e Limitações

### Limitações conhecidas

1. **Dataset de sensores pequeno:** o CSV histórico contém apenas 153 leituras do ESP32 Wokwi.
   Modelos de classificação ou regressão treinados diretamente sobre esses dados teriam alta variância.
   Por isso, o ML é treinado exclusivamente no dataset agronômico Cap10 (2.200 amostras).

2. **Domínio de aplicação:** os modelos foram treinados em condições de campo do dataset Cap10. As
   leituras do sensor ESP32 têm faixas de pH e temperatura que podem se afastar da distribuição de
   treino, reduzindo a confiabilidade das previsões nesses extremos.

3. **rainfall como proxy:** a variável-alvo não mede diretamente o volume de irrigação necessário por
   dia — é um indicador baseado em precipitação histórica associada à cultura. Recomendações baseadas
   nesse valor devem ser validadas por agrônomo.

4. **Dados simulados pelo scheduler:** as leituras geradas pelo APScheduler seguem a distribuição
   histórica do ESP32, mas são sintéticas. Não substituem dados reais de campo.

### Interpretação do R²

- R² próximo de 1.0: o modelo explica grande parte da variância do target.
- R² negativo: o modelo performa pior que simplesmente prever a média (indica problema de ajuste).
- Para `humidity`, esperamos R² alto pois há forte correlação com cultura e condições N/P/K.
- Para `rainfall`, o R² pode ser menor dado que precipitação tem maior variabilidade mesmo dentro
  da mesma cultura.

---

## 5. Simulação IoT com APScheduler

O `APScheduler` (versão 3.x, `BackgroundScheduler`) é iniciado uma única vez por sessão Streamlit
via `st.session_state`. A cada 30 segundos, um job gera valores com base na distribuição histórica
do sensor ESP32 (média e desvio por variável) e insere na tabela `leituras_sensores`. A lógica de
`bomba_fw` segue o mesmo critério do hardware: liga quando `umidade < UMIDADE_LIMIAR` (padrão: 60%).
