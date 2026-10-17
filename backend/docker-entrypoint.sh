#!/bin/sh
# Entrypoint бэкенда:
#   1) ждём, пока PostgreSQL станет доступен (до 60 секунд);
#   2) применяем миграции Alembic;
#   3) запускаем uvicorn.
set -e

echo "==> Waiting for database..."
python - <<'PY'
import sys
import time

from sqlalchemy import create_engine, text

from app.core.config import get_settings

settings = get_settings()
last_error = None

for attempt in range(60):
    try:
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("==> Database is ready")
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001 — любой коннект-еррор = «БД ещё не готова»
        last_error = exc
        time.sleep(1)

print(f"==> Database did not become ready in 60s: {last_error}", file=sys.stderr)
sys.exit(1)
PY

echo "==> Running migrations..."
alembic upgrade head

echo "==> Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
