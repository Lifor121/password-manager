import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column

Base = declarative_base()


class TimestampMixin:
    """Миксин для временных меток created_at и updated_at"""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )


class UUIDMixin:
    """Миксин для UUID первичных ключей"""
    
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))