# FIAP - Faculdade de Informática e Administração Paulista

<p align="center">
  <img src="assets/logo_fiap.webp" alt="FIAP" width="40%">
</p>

<br>

# FarmTech Solutions — Assistente Agrícola Inteligente

**Repositório:** [github.com/jojocamdb/FarmTech-Solutions-Fase4](https://github.com/jojocamdb/FarmTech-Solutions-Fase4/tree/main)

**Videos de apresentação:**
https://youtu.be/iBmst3sGG7I
--PARTE 1 – Integração de ML com Scikit-Learn e Streamlit em dashboard estática e online para gestores agrícolas

--PARTE 2 – Implementação de algoritmos preditivos para sugerir ações futuras de irrigação e manejo agrícola
https://youtu.be/xsXyGMQjZ_0
--PARTE 3 - IR ALÉM 1 – INTEGRAÇÃO DOS DADOS REAIS OU SIMULADOS IOT COM O BANCO DE DADOS
https://youtu.be/tG93NozbL6s
--PARTE 4 - IR ALÉM 2 – IR ALÉM 2 – DASHBOARD ANALÍTICO COM PREVISÕES INTERATIVA E ONLINE
https://youtu.be/iBmst3sGG7I


## 👨‍🎓 Integrantes

- Jocasta de Kacia Bortolacci — RM564730
- Marina Leme Soares — RM570461
- Carlos Magnus Costa Amaral — RM573978
- Georgia Mendes Rocha — RM573281
- Edemir Sufiatti — RM571375

## 👩‍🏫 Professores

### Tutor(a)

- Nicolly Cândida Rodrigues de Souza

### Coordenador(a)

- André Godoi Chiovato

---

## 📜 Descrição

O **FarmTech Solutions** é um Assistente Agrícola Inteligente desenvolvido para a Fase 4 do projeto FarmTech
da FIAP. A solução consolida dados de sensores IoT simulados no Wokwi em fases anteriores
com um pipeline de Machine Learning supervisionado (Scikit-Learn), entregando um dashboard interativo em
Streamlit apoiado por um banco de dados SQLite modelado de forma relacional e normalizada.
O Streamlit foi adotado por estar alinhado à orientação principal de dashboard interativo em Streamlit,
Power BI ou ferramenta similar.

O sistema parte de dois conjuntos de dados utilizados no protótipo: um conjunto de 153 leituras registradas/simuladas no contexto do ESP32/Wokwi (umidade, temperatura, pH, luminosidade, presença de N/P/K e estado da bomba de irrigação) e uma base agronômica de referência com 2.200 amostras de 22 culturas (N, P, K, temperatura, umidade, pH e precipitação). No módulo IoT, N/P/K são indicadores simplificados de presença do protótipo; no modelo de ML, N, P e K são valores numéricos do dataset agrícola usados como features de entrada.

Esses dados alimentam um banco SQLite com cinco tabelas normalizadas (`culturas`, `sensores`, `leituras_sensores`, `amostras_agronomicas`, `previsoes`), com integridade referencial garantida por chaves estrangeiras e consultas parametrizadas, reduzindo significativamente o risco de SQL injection.

Para simular a operação contínua do protótipo, um **scheduler** (APScheduler 3.x) gera novas leituras de sensor
a cada 30 segundos. A geração usa parâmetros aproximados definidos a partir do conjunto de leituras simuladas/registradas do protótipo e mantém a lógica de acionamento da bomba simulando a regra utilizada no firmware do ESP32 (liga quando a umidade cai abaixo do limiar configurado).

O núcleo de inteligência consiste em **dois modelos de regressão** treinados independentemente: um para
`rainfall` — interpretado como **proxy de necessidade hídrica** da cultura — e outro para `humidity` — a
umidade ambiental esperada. Cada modelo é resultado da comparação entre três algoritmos: `LinearRegression`
(baseline), `Ridge` (com `GridSearchCV` para ajuste do `alpha`) e `RandomForestRegressor`. As features (N, P,
K, temperatura, pH e cultura) passam por um `ColumnTransformer` com `OneHotEncoder` dentro de um `Pipeline`
do Scikit-Learn, garantindo um fluxo de pré-processamento reprodutível. A avaliação utiliza split treino/teste
80/20 com `random_state` fixo, validação cruzada K-Fold (k=5) e as métricas MAE, MSE, RMSE e R², além de análise de resíduos e interpretação da importância das variáveis quando disponível.

O dashboard é organizado em **sete páginas**: visão geral com status do banco e arquitetura; monitoramento
de leituras registradas/simuladas do protótipo ESP32/Wokwi; análise exploratória (heatmaps, distribuições, boxplots e scatter);
pipeline de ML com tabela comparativa, resíduos, feature importance quando aplicável e botão para retreinar; previsão interativa com formulário validado; recomendações de manejo que cruzam a previsão do modelo com as leituras registradas no banco (indicativos de bomba, ajuste de NPK e correção de pH, sempre com justificativa numérica
explícita); e histórico de previsões com exportação em CSV.

Uma premissa importante e documentada é que `rainfall` é tratado como **proxy de necessidade hídrica**,
e não como medição direta de lâmina de irrigação aplicada em campo nem como variável-alvo de produtividade.
Esta versão não prevê produtividade diretamente: a produtividade é tratada apenas de forma indireta, pelas
condições agronômicas analisadas e pelos indicativos simplificados de manejo. Da mesma forma, reconhece-se
que o dataset de 153 leituras de sensor é pequeno — por isso os modelos de ML são treinados exclusivamente
sobre o dataset agronômico de 2.200 amostras, reduzindo o risco de alta variância associado ao uso de uma
base muito pequena. Essas e outras limitações estão detalhadas em
`document/relatorio.md`.

O **`main.py`** na raiz do projeto centraliza a execução em um **menu interativo** que segue a ordem lógica
do pipeline (ingestão → ML → dashboard), exibe o status de cada etapa e permite rodar o fluxo completo ou
etapas isoladas, tanto pelo menu quanto por argumentos de linha de comando.

---

## 📁 Estrutura de pastas

Dentre os arquivos e pastas presentes na raiz do projeto, definem-se:

- **.github**: arquivos de configuração específicos do GitHub que ajudam a gerenciar e automatizar processos no repositório.

- **assets**: elementos não estruturados do repositório, como imagens e o logo da FIAP.

- **config**: arquivos de configuração com parâmetros do projeto. Contém `.env.example` com as variáveis de ambiente de referência (caminho do banco, limiar de umidade da bomba e intervalo do scheduler).

- **.streamlit**: configuração pública/neutra do Streamlit em `config.toml`. Porta, modo local e abertura do navegador são controlados pelo `main.py`.

- **document**: documentos do projeto. Contém `der.md` (Diagrama Entidade-Relacionamento em Mermaid com as decisões de modelagem) e `relatorio.md` (relatório técnico completo).

- **scripts**: scripts auxiliares para tarefas específicas. Contém `init_db.py`, que cria o schema do banco e realiza a carga inicial dos dois CSVs.

- **main.py**: launcher integrado na raiz do projeto. Oferece menu interativo do pipeline, verificação de
  status (banco SQLite e modelos `.joblib`), execução automática das etapas pendentes e atalhos CLI
  (`--pipeline`, `--ingestao`, `--treinar`, `--dashboard`). É o ponto de entrada recomendado da aplicação.

- **src**: todo o código-fonte criado para o desenvolvimento do projeto:
  - `dados/`: os dois datasets originais (`historico_irrigacao.csv` e `Atividade_Cap10_produtos_agricolas.csv`).
  - `db/`: módulo de acesso ao SQLite (`database.py`) e o arquivo `farmtech.db`, gerado localmente pela etapa de ingestão e não versionado no Git.
  - `ml/`: pipeline de treino (`train.py`) e os modelos persistidos em `models/` (`.joblib`, métricas em JSON e CSVs de diagnóstico).
  - `frontend/`: a aplicação Streamlit — `app.py` (Home e ponto de entrada), `scheduler.py` (simulação IoT) e as seis páginas em `pages/`.

- **README.md**: arquivo que serve como guia e explicação geral sobre o projeto (o mesmo que você está lendo agora).

---

## 🔧 Como executar o código

### Pré-requisitos

- Python 3.11 ou superior
- pip

### Forma recomendada local — `main.py` (menu do pipeline)

Após instalar as dependências, execute `python main.py` na raiz do projeto:

```bash
pip install -r requirements.txt
python main.py
```

Será exibido um **menu interativo** com o status de cada etapa e as opções do pipeline:

```
====================================================
  FarmTech Solutions — Menu do Pipeline
====================================================

  Status atual:
    [1] Banco SQLite ........ OK
    [2] Modelos ML .......... OK

  Pipeline (ordem do projeto):
    1 - Ingestao de dados (CSV -> SQLite)
    2 - Treinamento ML (Scikit-Learn)
    3 - Dashboard Streamlit
    4 - Pipeline completo (1 -> 2 -> 3)
    0 - Sair

Escolha uma opcao:
```

#### Opções do menu

| Opção | Etapa | O que faz |
|---|---|---|
| **1** | Ingestão | Carrega os CSVs em `src/dados/` para o SQLite via `scripts/init_db.py`. Se o banco já existir, pede confirmação antes de recriar. |
| **2** | ML | Treina os modelos de regressão via `src/ml/train.py`. Exige banco criado. Se os `.joblib` já existirem, pede confirmação antes de retreinar. |
| **3** | Dashboard | Abre o Streamlit em `src/frontend/app.py`. Exige banco e modelos prontos. |
| **4** | Pipeline completo | Executa automaticamente as etapas **1** e **2** somente se estiverem pendentes e, em seguida, abre o dashboard (**3**). |
| **0** | Sair | Encerra o programa. |

Após encerrar o dashboard com **Ctrl+C**, o menu é exibido novamente (no Windows o processo Streamlit é
finalizado corretamente).

#### Atalhos de linha de comando (sem menu)

Úteis em automações, Replit ou quando você já sabe qual etapa executar:

```bash
python main.py --pipeline     # etapas pendentes + dashboard (sem menu)
python main.py --ingestao     # força etapa 1 (recria o banco)
python main.py --treinar      # força etapa 2 (retreina os modelos)
python main.py --dashboard    # apenas etapa 3
python main.py --help         # lista todos os argumentos
```

| Flag | Comportamento |
|---|---|
| `--pipeline` | Modo automático: cria banco e treina modelos **somente se ausentes**, depois abre o dashboard. |
| `--ingestao` | Executa a ingestão **sem pedir confirmação** (recria `farmtech.db`). |
| `--treinar` | Executa o treinamento **sem pedir confirmação** (sobrescreve os `.joblib`). |
| `--dashboard` | Abre o Streamlit; falha com aviso se banco ou modelos não existirem. |

#### Ordem e dependências do pipeline

```
CSVs (src/dados/)
       │
       ▼  [1] init_db.py
SQLite (src/db/farmtech.db)
       │
       ▼  [2] train.py
Modelos (src/ml/models/*.joblib)
       │
       ▼  [3] Streamlit
Dashboard (src/frontend/app.py)
```

| Etapa | Arquivo gerado / usado | Condição no modo automático |
|---|---|---|
| 1 — Ingestão | `src/db/farmtech.db` | Roda se o banco **não existir** |
| 2 — ML | `modelo_rainfall.joblib`, `modelo_humidity.joblib` | Roda se algum `.joblib` **faltar** |
| 3 — Dashboard | — | Sempre executado ao final |

Os modelos treinados (`.joblib`) e artefatos de diagnóstico (`metricas.json`, `residuos_*.csv`) estão
versionados em `src/ml/models/`. O banco `farmtech.db` **não** vai para o Git — é gerado localmente na
etapa 1.

Ao executar novamente o treinamento, esses artefatos são regenerados e podem apresentar pequenas variações numéricas sem alterar necessariamente a conclusão técnica do modelo.

Acesse o dashboard localmente em `http://localhost:8501` (porta padrão local do `main.py`). Use `PORT`
apenas em deploy/servidor, quando a plataforma definir essa variável; não defina `PORT` no `.env` local.

**Windows (PowerShell):**

```powershell
cd <pasta-do-projeto>
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy config\.env.example .env   # opcional
python main.py
```

**Linux / Mac:**

```bash
cd <pasta-do-projeto>
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config/.env.example .env     # opcional
python main.py
```

### Execução no Replit

Configure o workflow para executar:

```bash
python main.py --pipeline
```

O flag `--pipeline` evita o menu interativo e garante setup automático na primeira execução antes de abrir
o dashboard no painel de preview.

### Execução manual (opcional)

Os scripts abaixo continuam disponíveis para uso direto, sem passar pelo `main.py`:

```bash
python scripts/init_db.py              # recria o banco e recarrega os CSVs
python src/ml/train.py                 # treina e persiste os modelos de ML
streamlit run src/frontend/app.py      # apenas o dashboard (porta 8501 por padrao)
```

---

## 🗃 Histórico de lançamentos

- 1.1.0 — 15/06/2026
  - Menu interativo no `main.py` com pipeline ordenado (ingestão → ML → dashboard).
  - Atalhos CLI: `--pipeline`, `--ingestao`, `--treinar`, `--dashboard`.
  - Encerramento do Streamlit com Ctrl+C corrigido no Windows.
  - Documentação de execução atualizada no README.

- 1.0.0 — 11/06/2026
  - Dashboard Streamlit completo com 7 páginas.
  - Banco SQLite normalizado (5 tabelas) com carga dos dois datasets.
  - Pipeline de ML com 3 modelos comparados para 2 targets (rainfall e humidity).
  - Scheduler IoT (APScheduler) com simulação de leituras a cada 30s.
  - Recomendações de manejo baseadas em regras agronômicas simplificadas para fins de protótipo acadêmico.
  - Documentação completa (DER e relatório técnico).

---

## 📋 Licença

<p>
  <img src="https://licensebuttons.net/l/by/4.0/88x31.png" alt="CC BY 4.0">
</p>

Este projeto FarmTech Solutions foi desenvolvido no contexto acadêmico da FIAP e está licenciado sob
[Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
