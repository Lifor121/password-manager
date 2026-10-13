from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from .user import User


class VaultItem(Base, UUIDMixin, TimestampMixin):
    """Модель зашифрованного элемента хранилища паролей"""
    
    __tablename__ = "vault_items"
    
    # Связь с пользователем
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    user: Mapped["User"] = relationship("User", back_populates="vault_items")
    
    # Зашифрованные данные
    encrypted_title: Mapped[str] = mapped_column(Text, nullable=False)  # Зашифрованное название сервиса
    title_blind_index: Mapped[str] = mapped_column(String(255), nullable=False, index=True)  # Слепой индекс для поиска
    
    encrypted_login: Mapped[str] = mapped_column(Text, nullable=False)  # Зашифрованный логин
    encrypted_password: Mapped[str] = mapped_column(Text, nullable=False)  # Зашифрованный пароль
    encrypted_url: Mapped[str | None] = mapped_column(Text, nullable=True)  # Зашифрованный URL
    encrypted_comment: Mapped[str | None] = mapped_column(Text, nullable=True)  # Зашифрованный комментарий
    
    def __repr__(self) -> str:
        return f"<VaultItem(id={self.id}, user_id={self.user_id}, blind_index={self.title_blind_index[:10]}...)>"
    
    def update_from_encrypted_data(
        self,
        encrypted_title: str,
        title_blind_index: str,
        encrypted_login: str,
        encrypted_password: str,
        encrypted_url: str | None = None,
        encrypted_comment: str | None = None
    ) -> None:
        """Обновление зашифрованных данных"""
        self.encrypted_title = encrypted_title
        self.title_blind_index = title_blind_index
        self.encrypted_login = encrypted_login
        self.encrypted_password = encrypted_password
        self.encrypted_url = encrypted_url
        self.encrypted_comment = encrypted_comment
    
    @property
    def has_url(self) -> bool:
        """Есть ли URL у элемента"""
        return self.encrypted_url is not None and self.encrypted_url != ""
    
    @property
    def has_comment(self) -> bool:
        """Есть ли комментарий у элемента"""
        return self.encrypted_comment is not None and self.encrypted_comment != ""
    
    def to_dict(self) -> dict:
        """Преобразование в словарь (без расшифровки)"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "encrypted_title": self.encrypted_title,
            "title_blind_index": self.title_blind_index,
            "encrypted_login": self.encrypted_login,
            "encrypted_password": self.encrypted_password,
            "encrypted_url": self.encrypted_url,
            "encrypted_comment": self.encrypted_comment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }