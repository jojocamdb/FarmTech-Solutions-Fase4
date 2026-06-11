"""
Script de inicialização do banco de dados FarmTech Solutions.
Cria o schema normalizado e carrega os dois CSVs.

Uso:
    python scripts/init_db.py
"""

import sqlite3
import csv
import os
import sys
from pathlib import Path

# Garante que a raiz do projeto está no path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "src/db/farmtech.db")
CSV_IRRIGACAO = ROOT / "src" / "dados" / "historico_irrigacao.csv"
CSV_AGRICOLA = ROOT / "src" / "dados" / "Atividade_Cap10_produtos_agricolas.csv"


DDL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS culturas (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS sensores (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo    TEXT NOT NULL,
    unidade TEXT NOT NULL,
    origem  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS leituras_sensores (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id INTEGER NOT NULL REFERENCES sensores(id),
    ts        TEXT    NOT NULL,
    umidade   REAL    NOT NULL,
    temp_c    REAL    NOT NULL,
    ldr       REAL    NOT NULL,
    ph        REAL    NOT NULL,
    n         INTEGER NOT NULL,
    p         INTEGER NOT NULL,
    k         INTEGER NOT NULL,
    bomba_fw  INTEGER NOT NULL CHECK (bomba_fw IN (0, 1))
);

CREATE TABLE IF NOT EXISTS amostras_agronomicas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    cultura_id  INTEGER NOT NULL REFERENCES culturas(id),
    n           REAL    NOT NULL,
    p           REAL    NOT NULL,
    k           REAL    NOT NULL,
    temperatura REAL    NOT NULL,
    umidade     REAL    NOT NULL,
    ph          REAL    NOT NULL,
    chuva       REAL    NOT NULL
);

CREATE TABLE IF NOT EXISTS previsoes (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    ts                 TEXT    NOT NULL,
    modelo             TEXT    NOT NULL,
    target             TEXT    NOT NULL,
    valor_previsto     REAL    NOT NULL,
    parametros_entrada TEXT    NOT NULL
);
"""


def criar_schema(conn: sqlite3.Connection) -> None:
    """Cria todas as tabelas se não existirem."""
    conn.executescript(DDL)
    conn.commit()
    print("[OK] Schema criado.")


def seed_sensores(conn: sqlite3.Connection) -> int:
    """Garante que o sensor ESP32 está cadastrado e retorna seu id."""
    row = conn.execute("SELECT id FROM sensores WHERE origem = 'ESP32'").fetchone()
    if row:
        return row[0]
    cur = conn.execute(
        "INSERT INTO sensores (tipo, unidade, origem) VALUES (?, ?, ?)",
        ("multiparâmetro", "misto", "ESP32"),
    )
    conn.commit()
    return cur.lastrowid


def carregar_irrigacao(conn: sqlite3.Connection, sensor_id: int) -> int:
    """Carrega historico_irrigacao.csv na tabela leituras_sensores."""
    count = 0
    with open(CSV_IRRIGACAO, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Ignora linhas de separador
            if "===" in row.get("ts_iso", ""):
                continue
            try:
                conn.execute(
                    """
                    INSERT INTO leituras_sensores
                        (sensor_id, ts, umidade, temp_c, ldr, ph, n, p, k, bomba_fw)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        sensor_id,
                        row["ts_iso"],
                        float(row["umidade"]),
                        float(row["temp_c"]),
                        float(row["ldr"]),
                        float(row["ph_corr"]),
                        int(row["N"]),
                        int(row["P"]),
                        int(row["K"]),
                        int(row["bomba_fw"]),
                    ),
                )
                count += 1
            except (ValueError, KeyError):
                continue
    conn.commit()
    print(f"[OK] {count} leituras de sensor carregadas.")
    return count


def carregar_agricola(conn: sqlite3.Connection) -> int:
    """Carrega Atividade_Cap10_produtos_agricolas.csv na tabela amostras_agronomicas."""
    cultura_ids: dict[str, int] = {}
    count = 0

    with open(CSV_AGRICOLA, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cultura = row["label"].strip()
            if cultura not in cultura_ids:
                # Upsert cultura
                conn.execute(
                    "INSERT OR IGNORE INTO culturas (nome) VALUES (?)", (cultura,)
                )
                r = conn.execute(
                    "SELECT id FROM culturas WHERE nome = ?", (cultura,)
                ).fetchone()
                cultura_ids[cultura] = r[0]

            conn.execute(
                """
                INSERT INTO amostras_agronomicas
                    (cultura_id, n, p, k, temperatura, umidade, ph, chuva)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cultura_ids[cultura],
                    float(row["N"]),
                    float(row["P"]),
                    float(row["K"]),
                    float(row["temperature"]),
                    float(row["humidity"]),
                    float(row["ph"]),
                    float(row["rainfall"]),
                ),
            )
            count += 1

    conn.commit()
    print(f"[OK] {count} amostras agronômicas carregadas ({len(cultura_ids)} culturas).")
    return count


def main() -> None:
    """Ponto de entrada principal."""
    db_file = Path(DB_PATH)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    if db_file.exists():
        print(f"[INFO] Banco existente em {DB_PATH}. Removendo para recriação limpa.")
        db_file.unlink()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    criar_schema(conn)
    sensor_id = seed_sensores(conn)
    carregar_irrigacao(conn, sensor_id)
    carregar_agricola(conn)

    conn.close()
    print(f"[OK] Banco inicializado em {DB_PATH}")


if __name__ == "__main__":
    main()
