"""Каркас эндпоинтов хранилища: валидация + rate limits.

Правило slowapi (headers_enabled=True): каждый эндпоинт с
@limiter.limit принимает ДВА служебных параметра:
  request: Request   — источник ключа лимита;
  response: Response — объект, куда slowapi вписывает X-RateLimit-*.
Без response — 500 "parameter `response` must be an instance of
starlette.responses.Response".

Авторизация — серверные сессии (таблица sessions): Bearer = UUID
сессии; Блок 2 проверяет её в БД и берёт user_id.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.core.config import get_settings
from app.core.rate_limit import limiter, session_key
from app.schemas.vault import (
    VaultItemCreate,
    VaultItemListResponse,
    VaultItemResponse,
)

settings = get_settings()
router = APIRouter(prefix="/vault", tags=["vault"])

# ВРЕМЕННОЕ in-memory хранилище. Блок 2 заменит его на БД.
_fake_db: dict[uuid.UUID, VaultItemResponse] = {}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@router.post(
    "/items",
    response_model=VaultItemResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(settings.rate_limit_write, key_func=session_key)
async def create_vault_item(
    request: Request, response: Response, payload: VaultItemCreate
) -> VaultItemResponse:
    # TODO(Блок 2): session = Depends(get_current_session):
    #   SELECT ... FROM sessions s JOIN users u ON u.id = s.user_id
    #   WHERE s.id = :bearer AND s.is_revoked = false AND s.expires_at > now()
    #   -> 401, если нет. INSERT INTO vault_items ... session.user_id.
    item = VaultItemResponse(
        id=uuid.uuid4(),
        created_at=_utcnow(),
        updated_at=_utcnow(),
        **payload.model_dump(),
    )
    _fake_db[item.id] = item
    return item


@router.get("/items", response_model=VaultItemListResponse)
@limiter.limit(settings.rate_limit_default)
async def list_vault_items(request: Request, response: Response) -> VaultItemListResponse:
    # TODO(Блок 2): WHERE user_id = session.user_id
    items = list(_fake_db.values())
    return VaultItemListResponse(items=items, total=len(items))


@router.get("/items/{item_id}", response_model=VaultItemResponse)
@limiter.limit(settings.rate_limit_default)
async def get_vault_item(
    request: Request, response: Response, item_id: uuid.UUID
) -> VaultItemResponse:
    # TODO(Блок 2): WHERE id = :item_id AND user_id = session.user_id
    # -> 404 (не 403: не раскрываем, существует ли чужая карточка)
    item = _fake_db.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
