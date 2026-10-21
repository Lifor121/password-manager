from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin

if TYPE_CHECKING:
    from .user import User


class Session(Base, UUIDMixin):
    """Модель сессии для Bearer-токенов аутентификации"""
    
    __tablename__ = "sessions"
    
    # Связь с пользователем
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    user: Mapped["User"] = relationship("User", back_populates="sessions")
    
    # Основные поля
    device_info: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Информация об устройстве
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<Session(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"
    
    @property
    def is_valid(self) -> bool:
        """Проверка валидности сессии"""
        return not self.is_revoked and self.expires_at > datetime.utcnow()
    
    @classmethod
    def create_session(
        cls, 
        user_id: str, 
        device_info: str | None = None, 
        ttl_hours: int = 12
    ) -> "Session":
        """Создание новой сессии"""
        # Обрезка device_info до 255 символов если нужно
        if device_info and len(device_info) > 255:
            device_info = device_info[:255]
        
        session = cls(
            user_id=user_id,
            device_info=device_info,
            expires_at=datetime.utcnow() + timedelta(hours=ttl_hours)
        )
        return session
    
    def revoke(self) -> None:
        """Отзыв сессии"""
        self.is_revoked = True
    
    def renew(self, ttl_hours: int = 12) -> None:
        """Продление сессии"""
        if self.is_valid:
            self.expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
    
    def time_remaining(self) -> timedelta:
        """Оставшееся время жизни сессии"""
        return self.expires_at - datetime.utcnow()