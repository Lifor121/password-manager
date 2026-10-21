"""
Rate limiting.

Ключи:
  - default (middleware): IP клиента — глобальный анти-DDoS порог;
  - сессионный: session_id из заголовка Authorization (Bearer);
    нет заголовка — IP.

Сессии живут в БД, но для лимитера туда ходить НЕ надо: сам Bearer
(= UUID сессии) — уже уникальный ключ. Подделка бессмысленна: рандомный
Bearer даёт рандомный ключ, а спам всё равно ловит IP-лимит.

IP берём из X-Forwarded-For: в production трафик идёт через
Nginx Proxy Manager (Блок 3), request.client.host был бы IP прокси.
"""
import logging

from fastapi import Request
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """IP клиента с учётом обратного прокси (Nginx Proxy Manager)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


def session_key(request: Request) -> str:
    """
    Ключ 'на клиента' для пишущих эндпоинтов (30/мин на сессию).

    У нас не JWT, а серверные сессии: Authorization содержит
    Bearer <session_id>. Ходить в БД ради user_id на каждый запрос
    не нужно — session_id сам отличный ключ (лимит 'на сессию').
    """
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        token = header[7:].strip()
        if token:
            return f"session:{token}"
    return f"ip:{get_client_ip(request)}"


async def rate_limit_exceeded_handler(request: Request, exc: Exception) -> JSONResponse:
    """429 в едином JSON-формате + Retry-After.

    Сигнатура обязана принимать `exc: Exception`, а не `RateLimitExceeded`:
    Starlette типизирует обработчики как Callable[[Request, Exception], ...],
    и строгий анализатор справедливо считает более узкий параметр
    несовместимым. Конкретный тип проверяем внутри через isinstance.
    """
    retry_after = 60
    if isinstance(exc, RateLimitExceeded):
        period = getattr(getattr(exc, "limit", None), "reset", None)
        if isinstance(period, (int, float)) and period > 0:
            retry_after = int(period)
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please slow down."},
        headers={"Retry-After": str(retry_after)},
    )


settings = get_settings()

limiter = Limiter(
    key_func=get_client_ip,
    default_limits=[settings.rate_limit_default],
    storage_uri=(settings.rate_limit_storage_uri or None),
    headers_enabled=True,
)
