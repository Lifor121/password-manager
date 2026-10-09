"""Схемы авторизации по согласованному контракту.

Мастер-пароль на сервер НЕ приходит: клиент сам считает KDF-хеш
(master_password_hash) и сам шифрует ключ хранилища мастер-паролем
(encrypted_vault_key). Серверная валидация здесь — только форматы и
длины; силу мастер-пароля проверяет фронтенд ДО хеширования (zxcvbn).
"""
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

EMAIL_MAX = 254  # максимум длины по RFC 5321

# Формат зависит от выбора KDF у бэкендера 1 (hex SHA-256 = 64 символа,
# base64 PBKDF2, строка Argon2 и т.п.). Пока — разумные границы;
# после фиксации KDF сузим до точной длины (это TODO для Блока auth).
CREDENTIAL_MIN = 16
CREDENTIAL_MAX = 512


def _clean_credential(value: str) -> str:
    """Хеши/ключи: без пробелов и управляющих символов."""
    if not value:
        raise ValueError("must not be empty")
    if any(ch.isspace() or ord(ch) < 33 for ch in value):
        raise ValueError("must not contain whitespace or control characters")
    return value


def _normalize_email(value: Any) -> Any:
    if isinstance(value, str):
        value = value.strip().lower()
    return value


class RegisterRequest(BaseModel):
    """POST /api/auth/register"""
    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(max_length=EMAIL_MAX)
    master_password_hash: str = Field(min_length=CREDENTIAL_MIN, max_length=CREDENTIAL_MAX)
    encrypted_vault_key: str = Field(min_length=CREDENTIAL_MIN, max_length=CREDENTIAL_MAX)
    crypto_salt: str = Field(min_length=8, max_length=CREDENTIAL_MAX)

    @field_validator("email", mode="before")
    @classmethod
    def _clean_email(cls, v):
        return _normalize_email(v)

    @field_validator("master_password_hash", "encrypted_vault_key", "crypto_salt")
    @classmethod
    def _clean_credentials(cls, v: str) -> str:
        return _clean_credential(v)


class LoginRequest(BaseModel):
    """POST /api/auth/login"""
    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(max_length=EMAIL_MAX)
    master_password_hash: str = Field(min_length=CREDENTIAL_MIN, max_length=CREDENTIAL_MAX)

    @field_validator("email", mode="before")
    @classmethod
    def _clean_email(cls, v):
        return _normalize_email(v)

    @field_validator("master_password_hash")
    @classmethod
    def _clean_credentials(cls, v: str) -> str:
        return _clean_credential(v)


class LoginResponse(BaseModel):
    """200 от POST /api/auth/login (для документации OpenAPI)."""
    access_token: str
    encrypted_vault_key: str
    crypto_salt: str


class ChangePasswordRequest(BaseModel):
    """PUT /api/users/me/password"""
    model_config = ConfigDict(extra="forbid")

    old_password_hash: str = Field(min_length=CREDENTIAL_MIN, max_length=CREDENTIAL_MAX)
    new_password_hash: str = Field(min_length=CREDENTIAL_MIN, max_length=CREDENTIAL_MAX)
    new_encrypted_vault_key: str = Field(min_length=CREDENTIAL_MIN, max_length=CREDENTIAL_MAX)

    @field_validator("old_password_hash", "new_password_hash", "new_encrypted_vault_key")
    @classmethod
    def _clean_credentials(cls, v: str) -> str:
        return _clean_credential(v)
