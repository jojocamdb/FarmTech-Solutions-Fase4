# FIAP - Faculdade de Informática e Administração Paulista

<p align="center">
  <img src="assets/logo_fiap.webp" alt="FIAP" width="40%">
</p>

<br>

# FarmTech Solutions — Assistente Agrícola Inteligente

## Grupo 47

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
da FIAP. A solução consolida dados de sensores IoT (ESP32 simulado no Wokwi, oriundo das fases anteriores)
com um pipeline de Machine Learning supervisionado (Scikit-Learn), entregando um dashboard interativo em
Streamlit apoiado por um banco de dados SQLite modelado de forma relacional e normalizada.

O sistema parte de dois conjuntos de dados reais: 154 leituras do sensor ESP32 (umidade, temperatura, pH,
luminosidade, presença de N/P/K e estado da bomba de irrigação) e 2.200 amostras agronômicas de 22 culturas
(N, P, K, temperatura, umidade, pH e precipitação). Esses dados alimentam um banco SQLite com cinco tabelas
normalizadas (`culturas`, `sensores`, `leituras_sensores`, `amostras_agronomicas`, `previsoes`), com
integridade referencial garantida por chaves estrangeiras e queries 100% parametrizadas — eliminando
qualquer risco de SQL injection.

Para simular a operação contínua de campo, um **scheduler** (APScheduler 3.x) gera novas leituras de sensor
a cada 30 segundos, derivadas da distribuição estatística (média e desvio) das leituras históricas, com a
lógica de acionamento da bomba reproduzindo o comportamento do firmware do ESP32 (liga quando a umidade cai
abaixo do limiar configurado).

O núcleo de inteligência consiste em **dois modelos de regressão** treinados independentemente: um para
`rainfall` — interpretado como **proxy de necessidade hídrica** da cultura — e outro para `humidity` — a
umidade ambiental esperada. Cada modelo é resultado da comparação entre três algoritmos: `LinearRegression`
(baseline), `Ridge` (com `GridSearchCV` para ajuste do `alpha`) e `RandomForestRegressor`. As features (N, P,
K, temperatura, pH e cultura) passam por um `ColumnTransformer` com `OneHotEncoder` dentro de um `Pipeline`
do Scikit-Learn, garantindo um fluxo de pré-processamento reprodutível. A avaliação utiliza split treino/teste
80/20 com `random_state` fixo, validação cruzada K-Fold (k=5) e as métricas MAE, MSE, RMSE e R², além de
análise de resíduos e feature importance.

O dashboard é organizado em **sete páginas**: visão geral com status do banco e arquitetura; monitoramento
de sensores IoT em tempo quase real; análise exploratória (heatmaps, distribuições, boxplots e scatter);
pipeline de ML com tabela comparativa, resíduos, feature importance e botão para retreinar; previsão em tempo
real com formulário validado; recomendações de manejo que cruzam a previsão do modelo com as leituras reais
dos sensores (acionamento de bomba, ajuste de NPK e correção de pH, sempre com justificativa numérica
explícita); e histórico de previsões com exportação em CSV.

Uma premissa importante e documentada é que `rainfall` é tratado como **interpretação de necessidade
hídrica**, e não como medida direta de rendimento. Da mesma forma, reconhece-se que o dataset de 154 leituras
de sensor é pequeno — por isso os modelos de ML são treinados exclusivamente sobre o dataset agronômico de
2.200 amostras, evitando alta variância. Essas e outras limitações estão detalhadas em
`document/relatorio.md`.

---

## 📁 Estrutura de pastas

Dentre os arquivos e pastas presentes na raiz do projeto, definem-se:

- **.github**: arquivos de configuração específicos do GitHub que ajudam a gerenciar e automatizar processos no repositório.

- **assets**: elementos não estruturados do repositório, como imagens e o logo da FIAP.

- **config**: arquivos de configuração com parâmetros do projeto. Contém `.env.example` com as variáveis de ambiente de referência (caminho do banco, limiar de umidade da bomba e intervalo do scheduler).

- **document**: documentos do projeto. Contém `der.md` (Diagrama Entidade-Relacionamento em Mermaid com as decisões de modelagem) e `relatorio.md` (relatório técnico completo).

- **scripts**: scripts auxiliares para tarefas específicas. Contém `init_db.py`, que cria o schema do banco e realiza a carga inicial dos dois CSVs.

- **src**: todo o código-fonte criado para o desenvolvimento do projeto:
  - `dados/`: os dois datasets originais (`historico_irrigacao.csv` e `Atividade_Cap10_produtos_agricolas.csv`).
  - `db/`: módulo de acesso ao banco SQLite (`database.py`) e o arquivo `farmtech.db` gerado.
  - `ml/`: pipeline de treino (`train.py`) e os modelos persistidos em `models/` (`.joblib`, métricas em JSON e CSVs de diagnóstico).
  - `frontend/`: a aplicação Streamlit — `app.py` (Home e ponto de entrada), `scheduler.py` (simulação IoT) e as seis páginas em `pages/`.

- **README.md**: arquivo que serve como guia e explicação geral sobre o projeto (o mesmo que você está lendo agora).

---

## 🔧 Como executar o código

### Pré-requisitos

- Python 3.11 ou superior
- pip

### Execução no Replit

A aplicação já está configurada para subir automaticamente via workflow. O banco de dados e os modelos de ML
são gerados na primeira execução. Para reinicializá-los manualmente, abra o Shell e execute:

```bash
python scripts/init_db.py   # recria o banco e carrega os CSVs
python src/ml/train.py      # treina e persiste os modelos de ML
```

O dashboard fica disponível no painel de preview do Replit.

### Execução local

```bash
# 1. Clonar o repositório
git clone <url-do-repositorio>
cd <pasta-do-projeto>

# 2. Criar e ativar um ambiente virtual
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
.venv\Scripts\activate         # Windows

# 3. Instalar as dependências
pip install -r requirements.txt

# 4. (Opcional) Configurar variáveis de ambiente
cp config/.env.example .env

# 5. Inicializar o banco de dados
python scripts/init_db.py

# 6. Treinar os modelos de ML
python src/ml/train.py

# 7. Iniciar o dashboard
streamlit run src/frontend/app.py
```

Acesse o dashboard em `http://localhost:8501` (local) ou na porta indicada pelo Streamlit.

---

## 🗃 Histórico de lançamentos

- 1.0.0 — 11/06/2026
  - Dashboard Streamlit completo com 7 páginas.
  - Banco SQLite normalizado (5 tabelas) com carga dos dois datasets.
  - Pipeline de ML com 3 modelos comparados para 2 targets (rainfall e humidity).
  - Scheduler IoT (APScheduler) com simulação de leituras a cada 30s.
  - Recomendações de manejo baseadas em regras agronômicas.
  - Documentação completa (DER e relatório técnico).

---

## 📋 Licença

<p>
  <img src="https://licensebuttons.net/l/by/4.0/88x31.png" alt="CC BY 4.0">
</p>

Este projeto FarmTech Solutions, desenvolvido por **Grupo 47 / FIAP**, está licenciado sobre
[Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
