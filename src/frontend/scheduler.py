"""
Scheduler de simulação IoT — insere leituras simuladas a cada 30 segundos.
Gerenciado via st.session_state para não duplicar jobs no Streamlit.
"""

import os
import random
import time
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
from dotenv import load_dotenv

load_dotenv()

UMIDADE_LIMIAR = float(os.getenv("UMIDADE_LIMIAR", "60.0"))
INTERVALO = int(os.getenv("SCHEDULER_INTERVALO", "30"))

# Parâmetros da distribuição histórica (calculados do CSV real)
_DIST = {
    "umidade":  {"media": 73.5,  "desvio": 12.0,  "min": 30.0, "max": 95.0},
    "temp_c":   {"media": 28.5,  "desvio": 5.5,   "min": 14.0, "max": 40.0},
    "ldr":      {"media": 1800.0,"desvio": 600.0,  "min": 1000.0,"max": 2531.0},
    "ph":       {"media": 7.2,   "desvio": 1.8,   "min": 4.5,  "max": 10.5},
}


def _gerar_leitura() -> dict:
    """Gera uma leitura simulada com base na distribuição histórica."""
    def sample(chave: str) -> float:
        d = _DIST[chave]
        v = np.random.normal(d["media"], d["desvio"])
        return float(np.clip(v, d["min"], d["max"]))

    umidade = round(sample("umidade"), 1)
    temp_c  = round(sample("temp_c"), 1)
    ldr     = round(sample("ldr"), 0)
    ph      = round(sample("ph"), 3)
    n = random.randint(0, 1)
    p = random.randint(0, 1)
    k = random.randint(0, 1)
    bomba_fw = 1 if umidade < UMIDADE_LIMIAR else 0

    return dict(umidade=umidade, temp_c=temp_c, ldr=ldr, ph=ph, n=n, p=p, k=k, bomba_fw=bomba_fw)


def iniciar_scheduler(scheduler_holder: dict) -> None:
    """
    Inicia o APScheduler se ainda não estiver rodando.
    scheduler_holder é um dicionário mutável de st.session_state.
    """
    from apscheduler.schedulers.background import BackgroundScheduler
    from src.db.database import inserir_leitura_simulada

    if scheduler_holder.get("scheduler") is not None:
        return

    def job():
        leitura = _gerar_leitura()
        inserir_leitura_simulada(**leitura)

    sched = BackgroundScheduler()
    sched.add_job(job, "interval", seconds=INTERVALO, id="simulacao_iot")
    sched.start()
    scheduler_holder["scheduler"] = sched
    scheduler_holder["iniciado_em"] = time.time()
