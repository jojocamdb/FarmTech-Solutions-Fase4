"""
FarmTech Solutions — ponto de entrada integrado com menu de pipeline.

Ordem do pipeline:
    1. Ingestao CSV -> SQLite
    2. Treinamento ML (Scikit-Learn)
    3. Dashboard Streamlit

Uso:
    python main.py              # menu interativo
    python main.py --pipeline     # executa etapas pendentes + dashboard
    python main.py --ingestao     # apenas etapa 1
    python main.py --treinar      # apenas etapa 2
    python main.py --dashboard    # apenas etapa 3
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent
MODELS_DIR = ROOT / "src" / "ml" / "models"
REQUIRED_MODELS = ("modelo_rainfall.joblib", "modelo_humidity.joblib")

MENU_WIDTH = 52


def db_path() -> str:
    return os.getenv("DB_PATH", "src/db/farmtech.db")


def status_banco() -> bool:
    return os.path.exists(db_path())


def status_modelos() -> tuple[bool, list[str]]:
    missing = [name for name in REQUIRED_MODELS if not (MODELS_DIR / name).exists()]
    return len(missing) == 0, missing


def _run_script(relative_path: str, label: str) -> None:
    script = ROOT / relative_path
    print(f"\n[{label}] Executando {relative_path} ...", flush=True)
    subprocess.run([sys.executable, str(script)], check=True, cwd=ROOT)
    print(f"[{label}] Concluido.", flush=True)


def etapa_ingestao(*, force: bool = False) -> None:
    """Etapa 1 — CSVs -> SQLite."""
    if status_banco() and not force:
        resp = input("Banco ja existe. Recriar e recarregar CSVs? [s/N]: ").strip().lower()
        if resp not in ("s", "sim"):
            print("[1/3] Ingestao cancelada.")
            return
    _run_script("scripts/init_db.py", "1/3 Ingestao")


def etapa_treinamento(*, force: bool = False) -> None:
    """Etapa 2 — treino e persistencia dos modelos."""
    if not status_banco():
        print("[2/3] Banco nao encontrado. Execute a etapa 1 primeiro.")
        return
    ok, _ = status_modelos()
    if ok and not force:
        resp = input("Modelos ja existem. Retreinar? [s/N]: ").strip().lower()
        if resp not in ("s", "sim"):
            print("[2/3] Treinamento cancelado.")
            return
    _run_script("src/ml/train.py", "2/3 ML")


def ensure_database() -> None:
    """Cria banco apenas se ausente (modo pipeline automatico)."""
    if status_banco():
        return
    _run_script("scripts/init_db.py", "1/3 Ingestao")


def ensure_models() -> None:
    """Treina modelos apenas se ausentes (modo pipeline automatico)."""
    missing = [name for name in REQUIRED_MODELS if not (MODELS_DIR / name).exists()]
    if not missing:
        return
    print(f"[2/3] Modelos ausentes: {', '.join(missing)}", flush=True)
    _run_script("src/ml/train.py", "2/3 ML")


def etapa_dashboard() -> None:
    """Etapa 3 — dashboard Streamlit."""
    if not status_banco():
        print("[3/3] Banco nao encontrado. Execute a etapa 1 primeiro.")
        return
    ok, missing = status_modelos()
    if not ok:
        print(f"[3/3] Modelos ausentes: {', '.join(missing)}. Execute a etapa 2 primeiro.")
        return
    run_streamlit()


def run_streamlit() -> None:
    """Inicia o dashboard Streamlit."""
    port = os.environ.get("PORT", "8080")
    print(f"\n[3/3 Dashboard] http://localhost:{port}", flush=True)
    print("[3/3 Dashboard] Pressione Ctrl+C para encerrar.\n", flush=True)

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "src/frontend/app.py",
        "--server.port",
        port,
        "--server.address",
        "0.0.0.0",
        "--server.headless",
        "true",
        "--server.enableCORS",
        "false",
        "--server.enableXsrfProtection",
        "false",
    ]

    if os.name != "nt":
        os.execv(sys.executable, cmd)

    proc = subprocess.Popen(cmd, cwd=ROOT)
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\n[3/3 Dashboard] Encerrando Streamlit...", flush=True)
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )


def pipeline_completo() -> None:
    """Executa 1 -> 2 -> 3 (somente o que estiver pendente, depois abre o dashboard)."""
    ensure_database()
    ensure_models()
    etapa_dashboard()


def _status_label(ok: bool) -> str:
    return "OK" if ok else "PENDENTE"


def exibir_menu() -> None:
    banco_ok = status_banco()
    modelos_ok, _ = status_modelos()

    print()
    print("=" * MENU_WIDTH)
    print("  FarmTech Solutions — Menu do Pipeline")
    print("=" * MENU_WIDTH)
    print()
    print("  Status atual:")
    print(f"    [1] Banco SQLite ........ {_status_label(banco_ok)}")
    print(f"    [2] Modelos ML .......... {_status_label(modelos_ok)}")
    print()
    print("  Pipeline (ordem do projeto):")
    print("    1 - Ingestao de dados (CSV -> SQLite)")
    print("    2 - Treinamento ML (Scikit-Learn)")
    print("    3 - Dashboard Streamlit")
    print("    4 - Pipeline completo (1 -> 2 -> 3)")
    print("    0 - Sair")
    print()


def menu_interativo() -> None:
    """Loop do menu ate o usuario sair ou encerrar o dashboard."""
    os.chdir(ROOT)

    while True:
        exibir_menu()
        try:
            opcao = input("Escolha uma opcao: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando.")
            return

        if opcao == "0":
            print("Ate logo.")
            return
        if opcao == "1":
            etapa_ingestao()
        elif opcao == "2":
            etapa_treinamento()
        elif opcao == "3":
            etapa_dashboard()
        elif opcao == "4":
            pipeline_completo()
        else:
            print("Opcao invalida. Use 0, 1, 2, 3 ou 4.")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="FarmTech Solutions — launcher do pipeline agricola"
    )
    parser.add_argument(
        "--pipeline",
        action="store_true",
        help="executa etapas pendentes e abre o dashboard (sem menu)",
    )
    parser.add_argument(
        "--ingestao",
        action="store_true",
        help="apenas etapa 1: CSV -> SQLite",
    )
    parser.add_argument(
        "--treinar",
        action="store_true",
        help="apenas etapa 2: treinamento ML",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="apenas etapa 3: dashboard Streamlit",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    os.chdir(ROOT)
    args = parse_args(argv)

    if args.pipeline:
        pipeline_completo()
        return
    if args.ingestao:
        etapa_ingestao(force=True)
        return
    if args.treinar:
        etapa_treinamento(force=True)
        return
    if args.dashboard:
        etapa_dashboard()
        return

    menu_interativo()


if __name__ == "__main__":
    main()
