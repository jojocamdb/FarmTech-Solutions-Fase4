import os
import subprocess
import sys


def ensure_database():
    db_path = os.getenv("DB_PATH", "src/db/farmtech.db")
    if not os.path.exists(db_path):
        subprocess.run([sys.executable, "scripts/init_db.py"], check=True)


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    ensure_database()
    port = os.environ.get("PORT", "8080")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "src/frontend/app.py",
        "--server.port", port,
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false",
    ])


if __name__ == "__main__":
    main()
