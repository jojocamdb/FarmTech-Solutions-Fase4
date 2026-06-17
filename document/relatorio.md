# Relatório Técnico — FarmTech Solutions
## Fase 4 — Assistente Agrícola Inteligente

**FIAP — Tecnólogo em Inteligência Artificial**
Junho de 2026

---

## 1. Modelagem do Banco de Dados

### Estrutura relacional

O banco SQLite (`farmtech.db`) é composto por cinco tabelas normalizadas:

- **culturas** — catálogo de 22 culturas do dataset agronômico.
- **sensores** — cadastro de sensores IoT; permite registrar múltiplos dispositivos.
- **leituras_sensores** — 153 leituras registradas/simuladas do protótipo ESP32/Wokwi + leituras sintéticas geradas pelo APScheduler.
- **amostras_agronomicas** — 2.200 amostras do dataset Cap10, vinculadas às culturas.
- **previsoes** — histórico das previsões registradas via interface.

A separação em tabelas distintas reduz redundância e organiza a integridade referencial por meio de chaves estrangeiras. Na camada de acesso ao banco, o projeto habilita `PRAGMA foreign_keys = ON`, e as operações revisadas utilizam consultas parametrizadas, reduzindo o risco de SQL injection.


### Script de inicialização

`scripts/init_db.py` lê os dois CSVs, cria o schema e popula o banco em uma única execução. A linha de
separação `===` presente no CSV de irrigação é ignorada via verificação explícita no parser.

---

## 2. Premissas dos Targets de ML

### rainfall — proxy de necessidade hídrica

**Importante:** `rainfall` representa a precipitação pluviométrica histórica associada às condições de cultivo do dataset agronômico. Neste projeto, a variável é usada como proxy para apoiar a análise de necessidade hídrica, mas não corresponde diretamente ao volume de irrigação que deve ser aplicado no campo.

Essa interpretação é uma aproximação prática para fins de protótipo acadêmico. Valores mais altos de `rainfall` podem indicar culturas ou condições historicamente associadas a maior disponibilidade hídrica, mas a decisão de irrigação deve considerar também as leituras dos sensores, a umidade do solo, o estágio da cultura e a validação agronômica local.

### humidity — umidade ambiental esperada

`humidity` representa a umidade relativa do ar associada às condições de cultivo registradas no dataset agronômico, considerando N, P, K, temperatura, pH e cultura. No protótipo, essa previsão é usada como referência comparativa em relação às leituras simuladas dos sensores, apoiando recomendações simplificadas de manejo. A variável não deve ser interpretada como medição em tempo real nem como recomendação agronômica conclusiva.

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
- **Feature importance:** exibida apenas quando o modelo selecionado permite esse tipo de interpretação, como no caso do `RandomForestRegressor`. Nos treinamentos em que o modelo selecionado for linear ou regularizado, essa análise não é apresentada como explicação principal.

### Persistência

Os pipelines selecionados pelo maior R² no conjunto de teste são salvos em `src/ml/models/modelo_<target>.joblib`. As métricas são registradas em `src/ml/models/metricas.json`, permitindo que o dashboard consulte os resultados do treinamento sem reexecutar o pipeline a cada acesso.


---

## 4. Interpretação das Métricas e Limitações

### Limitações conhecidas

1. **Dataset de sensores pequeno:** o CSV de irrigação contém apenas 153 leituras registradas/simuladas do protótipo ESP32/Wokwi.
   Modelos de classificação ou regressão treinados diretamente sobre esses dados teriam alta variância.
   Por isso, o ML é treinado exclusivamente no dataset agronômico Cap10 (2.200 amostras).

2. **Domínio de aplicação:** os modelos foram treinados em condições de campo do dataset Cap10. As
   leituras do sensor ESP32 têm faixas de pH e temperatura que podem se afastar da distribuição de
   treino, reduzindo a confiabilidade das previsões nesses extremos.

3. **rainfall como proxy:** a variável-alvo não mede diretamente o volume de irrigação necessário por
   dia — é um indicador baseado em precipitação histórica associada à cultura. Recomendações baseadas
   nesse valor devem ser validadas por agrônomo.

4. **Dados simulados pelo scheduler:** as leituras geradas pelo APScheduler usam parâmetros baseados
   no conjunto de leituras registradas/simuladas do protótipo, mas são sintéticas. Não substituem validação agronômica com medições de campo.

### Interpretação dos resultados do treinamento

No treinamento atual, o modelo `Ridge` foi selecionado para os dois targets por apresentar o maior R² no conjunto de teste. Para `rainfall`, o Ridge obteve MAE de aproximadamente 14,35, RMSE de 23,16 e R² de 0,8219. Para `humidity`, obteve MAE de aproximadamente 3,10, RMSE de 4,54 e R² de 0,9617.

A diferença entre `LinearRegression` e `Ridge` foi pequena nos dois casos, o que indica que a regularização L2 trouxe ganho marginal, mas suficiente para ser selecionada pelo critério definido no pipeline. O `RandomForestRegressor`, embora útil como modelo comparativo, apresentou R² inferior para os dois targets neste treinamento.

O desempenho de `humidity` foi mais alto que o de `rainfall`, sugerindo que a umidade apresenta relação mais estável com as variáveis disponíveis no dataset. Já `rainfall` tende a ser mais variável, pois representa precipitação histórica associada às condições da cultura e não um volume direto de irrigação recomendado.

---

## 5. Simulação IoT com APScheduler

O `APScheduler` (versão 3.x, `BackgroundScheduler`) é iniciado uma única vez por sessão Streamlit via `st.session_state`. A cada 30 segundos, um job gera valores sintéticos com parâmetros baseados no conjunto de leituras registradas/simuladas do protótipo ESP32/Wokwi, considerando média e desvio por variável, e insere os registros na tabela `leituras_sensores`.

A lógica de `bomba_fw` simula o critério utilizado no protótipo: a bomba é acionada quando `umidade < UMIDADE_LIMIAR`, com limiar padrão de 60%. Essa simulação apoia a visualização do fluxo IoT no dashboard, mas não substitui validação agronômica com medições de campo.
