"""Схемы карточек по структуре таблицы vault_items.

Каждое поле карточки шифруется на клиенте ОТДЕЛЬНО (AES-GCM со своим
nonce на поле) — поэтому полей несколько, а не один блоб. Сервер видит
только base64-шифртексты: проверяем длину и формат, содержание не знаем.
"""
import base64
import binascii
import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Base64 раздувает данные на ~1/3 — лимиты с запасом.
TITLE_CIPHERTEXT_MAX = 2048      # шифртекст названия
FIELD_CIPHERTEXT_MAX = 4096      # login / password / url / comment

_BASE64_RE = re.compile(r"^[A-Za-z0-9+/\-_]*={0,2}$")


def _validate_base64(value: str, max_len: int) -> str:
    value = value.strip()
    if not value:
        raise ValueError("ciphertext must not be empty")
    if len(value) > max_len:
        raise ValueError(f"ciphertext is too long (max {max_len} chars)")
    if not _BASE64_RE.fullmatch(value):
        raise ValueError("value must be a valid base64 string")
    normalized = value.replace("-", "+").replace("_", "/")
    normalized += "=" * (-len(normalized) % 4)
    try:
        base64.b64decode(normalized, validate=True)
    except (binascii.Error, ValueError):
        raise ValueError("value must be a valid base64 string")
    return value


class VaultItemCreate(BaseModel):
    """POST /api/vault/items и PUT /api/vault/items/{id} (полная перезапись)."""
    model_config = ConfigDict(extra="forbid")

    encrypted_title: str = Field(min_length=1, max_length=TITLE_CIPHERTEXT_MAX)
    encrypted_password: str = Field(min_length=1, max_length=FIELD_CIPHERTEXT_MAX)
    encrypted_login: Optional[str] = Field(default=None, max_length=FIELD_CIPHERTEXT_MAX)
    encrypted_url: Optional[str] = Field(default=None, max_length=FIELD_CIPHERTEXT_MAX)
    encrypted_comment: Optional[str] = Field(default=None, max_length=FIELD_CIPHERTEXT_MAX)
    # Слепой индекс для СЕРВЕРНОГО поиска по названию. Считает КЛИЕНТ:
    # HMAC-SHA256(нормализованный title, ключ выведен из vault_key) —
    # ключа нет у сервера, иначе смысл индекса теряется (утечка БД +
    # ключа = перебор популярных названий). Поиск на клиенте — не шлём.
    title_blind_index: Optional[str] = None

    @field_validator("encrypted_title")
    @classmethod
    def _check_title(cls, v: str) -> str:
        return _validate_base64(v, TITLE_CIPHERTEXT_MAX)

    @field_validator("encrypted_password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        return _validate_base64(v, FIELD_CIPHERTEXT_MAX)

    @field_validator("encrypted_login", "encrypted_url", "encrypted_comment")
    @classmethod
    def _check_optional_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        return _validate_base64(v, FIELD_CIPHERTEXT_MAX)

    @field_validator("title_blind_index")
    @classmethod
    def _check_blind_index(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        v = v.strip().lower()
        if not re.fullmatch(r"[0-9a-f]{16,64}", v):
            raise ValueError("title_blind_index must be 16-64 hex chars (HMAC-SHA256)")
        return v


class VaultItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # маппинг из ORM (Блок 2)

    id: UUID
    encrypted_title: str
    title_blind_index: Optional[str] = None
    encrypted_login: Optional[str] = None
    encrypted_password: str
    encrypted_url: Optional[str] = None
    encrypted_comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class VaultItemListResponse(BaseModel):
    items: list[VaultItemResponse]
    total: int
