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
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Response, status
from sqlalchemy import select

from app.api.deps import CurrentSession, DbSession
from app.core.config import get_settings
from app.core.rate_limit import limiter, session_key
from app.models.vault_item import VaultItem
from app.schemas.vault import (
    VaultItemCreate,
    VaultItemListResponse,
    VaultItemResponse,
)

settings = get_settings()
router = APIRouter(prefix="/vault", tags=["vault"])

@router.post(
    "/items",
    response_model=VaultItemResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(settings.rate_limit_write, key_func=session_key)
async def create_vault_item(
    request: Request,
    response: Response,
    payload: VaultItemCreate,
    current_session: CurrentSession,
    db: DbSession,
) -> VaultItemResponse:
    item = VaultItem(
        user_id=current_session.user_id,
        encrypted_title=payload.encrypted_title,
        encrypted_password=payload.encrypted_password,
        encrypted_login=payload.encrypted_login or "",
        title_blind_index=payload.title_blind_index or "",
        encrypted_url=payload.encrypted_url,
        encrypted_comment=payload.encrypted_comment,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return VaultItemResponse.model_validate(item)

@router.get("/items", response_model=VaultItemListResponse)
@limiter.limit(settings.rate_limit_default)
async def list_vault_items(
    request: Request,
    response: Response,
    current_session: CurrentSession,
    db: DbSession,
) -> VaultItemListResponse:
    stmt = (
        select(VaultItem)
        .where(VaultItem.user_id == current_session.user_id)
        .order_by(VaultItem.created_at.desc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    items = [VaultItemResponse.model_validate(row) for row in rows]
    return VaultItemListResponse(items=items, total=len(items))

@router.get("/items/{item_id}", response_model=VaultItemResponse)
@limiter.limit(settings.rate_limit_default)
async def get_vault_item(
    request: Request,
    response: Response,
    item_id: uuid.UUID,
    current_session: CurrentSession,
    db: DbSession,
) -> VaultItemResponse:
    stmt = select(VaultItem).where(
        VaultItem.id == str(item_id),
        VaultItem.user_id == current_session.user_id,
    )
    item = (await db.execute(stmt)).scalar_one_or_none()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    return VaultItemResponse.model_validate(item)

@router.put("/items/{item_id}", response_model=VaultItemResponse)
@limiter.limit(settings.rate_limit_write, key_func=session_key)
async def update_vault_item(
    request: Request,
    response: Response,
    item_id: uuid.UUID,
    payload: VaultItemCreate,
    current_session: CurrentSession,
    db: DbSession,
) -> VaultItemResponse:
    stmt = select(VaultItem).where(
        VaultItem.id == str(item_id),
        VaultItem.user_id == current_session.user_id,
    )
    item = (await db.execute(stmt)).scalar_one_or_none()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    item.update_from_encrypted_data(
        encrypted_title=payload.encrypted_title,
        title_blind_index=payload.title_blind_index or "",
        encrypted_login=payload.encrypted_login or "",
        encrypted_password=payload.encrypted_password,
        encrypted_url=payload.encrypted_url,
        encrypted_comment=payload.encrypted_comment,
    )
    item.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(item)
    return VaultItemResponse.model_validate(item)

@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
@limiter.limit(settings.rate_limit_write, key_func


=session_key)
async def delete_vault_item(
    request: Request,
    response: Response,
    item_id: uuid.UUID,
    current_session: CurrentSession,
    db: DbSession,
) -> Response:
    stmt = select(VaultItem).where(
        VaultItem.id == str(item_id),
        VaultItem.user_id == current_session.user_id,
    )
    item = (await db.execute(stmt)).scalar_one_or_none()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    await db.delete(item)
    await db.commit()
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
