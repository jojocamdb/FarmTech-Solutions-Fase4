"""
Módulo de acesso ao banco de dados SQLite do FarmTech Solutions.
Fornece conexão, queries parametrizadas e helpers para todas as tabelas.
"""

import sqlite3
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "src/db/farmtech.db")


def get_connection() -> sqlite3.Connection:
    """Retorna conexão com o banco SQLite com row_factory configurado."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def status_banco() -> dict:
    """Retorna contagem de registros por tabela."""
    tabelas = [
        "culturas",
        "sensores",
        "leituras_sensores",
        "amostras_agronomicas",
        "previsoes",
    ]
    resultado = {}
    with get_connection() as conn:
        for tabela in tabelas:
            try:
                row = conn.execute(f"SELECT COUNT(*) as total FROM {tabela}").fetchone()
                resultado[tabela] = row["total"] if row else 0
            except sqlite3.OperationalError:
                resultado[tabela] = 0
    return resultado


def get_leituras(limite: int = 200) -> list[dict]:
    """Retorna as últimas leituras dos sensores."""
    sql = """
        SELECT ls.id, ls.ts, ls.umidade, ls.temp_c, ls.ldr,
               ls.ph, ls.n, ls.p, ls.k, ls.bomba_fw,
               s.tipo as sensor_tipo
        FROM leituras_sensores ls
        JOIN sensores s ON s.id = ls.sensor_id
        ORDER BY ls.ts DESC
        LIMIT ?
    """
    with get_connection() as conn:
        rows = conn.execute(sql, (limite,)).fetchall()
    return [dict(r) for r in rows]


def get_ultima_leitura() -> dict | None:
    """Retorna a leitura mais recente."""
    sql = """
        SELECT ls.id, ls.ts, ls.umidade, ls.temp_c, ls.ldr,
               ls.ph, ls.n, ls.p, ls.k, ls.bomba_fw
        FROM leituras_sensores ls
        ORDER BY ls.ts DESC
        LIMIT 1
    """
    with get_connection() as conn:
        row = conn.execute(sql).fetchone()
    return dict(row) if row else None


def get_amostras_agronomicas() -> list[dict]:
    """Retorna todas as amostras agronômicas com nome da cultura."""
    sql = """
        SELECT aa.id, c.nome as cultura, aa.n, aa.p, aa.k,
               aa.temperatura, aa.umidade, aa.ph, aa.chuva
        FROM amostras_agronomicas aa
        JOIN culturas c ON c.id = aa.cultura_id
    """
    with get_connection() as conn:
        rows = conn.execute(sql).fetchall()
    return [dict(r) for r in rows]


def get_culturas() -> list[str]:
    """Retorna lista de nomes de culturas."""
    with get_connection() as conn:
        rows = conn.execute("SELECT nome FROM culturas ORDER BY nome").fetchall()
    return [r["nome"] for r in rows]


def inserir_previsao(modelo: str, target: str, valor: float, parametros: str) -> None:
    """Insere um registro na tabela previsoes."""
    sql = """
        INSERT INTO previsoes (ts, modelo, target, valor_previsto, parametros_entrada)
        VALUES (datetime('now'), ?, ?, ?, ?)
    """
    with get_connection() as conn:
        conn.execute(sql, (modelo, target, valor, parametros))
        conn.commit()


def get_previsoes(limite: int = 100) -> list[dict]:
    """Retorna histórico de previsões."""
    sql = """
        SELECT id, ts, modelo, target, valor_previsto, parametros_entrada
        FROM previsoes
        ORDER BY ts DESC
        LIMIT ?
    """
    with get_connection() as conn:
        rows = conn.execute(sql, (limite,)).fetchall()
    return [dict(r) for r in rows]


def inserir_leitura_simulada(
    umidade: float,
    temp_c: float,
    ldr: float,
    ph: float,
    n: int,
    p: int,
    k: int,
    bomba_fw: int,
    sensor_id: int = 1,
) -> None:
    """Insere uma leitura simulada na tabela leituras_sensores."""
    sql = """
        INSERT INTO leituras_sensores
            (sensor_id, ts, umidade, temp_c, ldr, ph, n, p, k, bomba_fw)
        VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?)
    """
    with get_connection() as conn:
        conn.execute(sql, (sensor_id, umidade, temp_c, ldr, ph, n, p, k, bomba_fw))
        conn.commit()


def mediana_cultura(cultura: str) -> dict | None:
    """Retorna a mediana de N, P, K e ph para uma cultura."""
    sql = """
        SELECT
            AVG(aa.n) as n_med,
            AVG(aa.p) as p_med,
            AVG(aa.k) as k_med,
            AVG(aa.ph) as ph_med
        FROM amostras_agronomicas aa
        JOIN culturas c ON c.id = aa.cultura_id
        WHERE c.nome = ?
    """
    with get_connection() as conn:
        row = conn.execute(sql, (cultura,)).fetchone()
    return dict(row) if row else None
