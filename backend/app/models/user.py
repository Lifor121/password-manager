from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .session import Session
    from .vault_item import VaultItem


class User(Base, UUIDMixin, TimestampMixin):
    """Модель пользователя с Zero-Knowledge аутентификацией"""
    
    __tablename__ = "users"
    
    # Основные поля
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    auth_hash: Mapped[str] = mapped_column(String(255), nullable=False)  # master_password_hash в hex формате
    crypto_salt: Mapped[str] = mapped_column(String(255), nullable=False)  # Соль для криптографических операций
    encrypted_vault_key: Mapped[str] = mapped_column(Text, nullable=False)  # Зашифрованный симметричный ключ хранилища
    
    # Связи
    sessions: Mapped[List["Session"]] = relationship(
        "Session", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    
    vault_items: Mapped[List["VaultItem"]] = relationship(
        "VaultItem", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
    
    @property
    def is_active(self) -> bool:
        """Проверка, активен ли пользователь"""
        return True  # В этой реализации все пользователи активны
    
    def check_password_hash(self, password_hash: str) -> bool:
        """Проверка хэша пароля"""
        return self.auth_hash == password_hash
    
    def update_password(self, new_auth_hash: str, new_encrypted_vault_key: str) -> None:
        """Обновление пароля и ключа хранилища"""
        self.auth_hash = new_auth_hash
        self.encrypted_vault_key = new_encrypted_vault_key
        self.updated_at = datetime.utcnow()