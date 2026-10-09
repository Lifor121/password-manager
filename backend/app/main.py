"""
Точка входа API.

Слои middleware (снаружи внутрь, в порядке обработки запроса):
  1. CORS       — пропускает preflight OPTIONS, добавляет CORS-заголовки
  2. SizeLimit  — 413 для тел больше MAX_REQUEST_BODY_BYTES
  3. SlowAPI    — rate limiting (default-лимиты на все роуты)
  4. Роуты      — + пер-роутовые лимиты через @limiter.limit(...)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.routes import health, vault
from app.core.config import get_settings
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.middleware.request_size_limit import RequestSizeLimitMiddleware

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url=None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
)

# --- Rate limiting (feat: setup rate limiting for API endpoints) ---------
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)  # default-лимиты на все эндпоинты

# --- Ограничение размера тела ---------------------------------------------
app.add_middleware(
    RequestSizeLimitMiddleware,
    max_body_bytes=settings.max_request_body_bytes,
)

# --- CORS (feat: add CORS middleware configuration) -----------------------
# Порядок важен: CORSMiddleware добавляется ПОСЛЕДНИМ => срабатывает ПЕРВЫМ
# (middleware в FastAPI — стек LIFO). Благодаря этому:
#   - preflight OPTIONS обрабатывается сразу и не тратит лимиты;
#   - ошибки 429/413/422 получают CORS-заголовки, и браузер показывает
#     фронтенду настоящий код ошибки, а не загадочную "CORS error".
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # только конкретные домены, без "*"
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    expose_headers=[  # чтобы фронт мог читать эти заголовки из ответа
        "Retry-After", "X-RateLimit-Limit",
        "X-RateLimit-Remaining", "X-RateLimit-Reset",
    ],
    max_age=3600,  # браузер кэширует результат preflight на час
)

# --- Роутеры ---------------------------------------------------------------
app.include_router(health.router)
app.include_router(vault.router, prefix=settings.api_prefix)
