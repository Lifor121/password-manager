from collections.abc import AsyncGenerator, Generator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.base import Base

settings = get_settings()


# Создание синхронного движка для Alembic и миграций
engine: Engine = create_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.database_echo,
)

# Создание асинхронного движка для FastAPI
async_engine = create_async_engine(
    settings.database_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://"),
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.database_echo,
)

# Синхронная фабрика сессий (для миграций и тестов)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Асинхронная фабрика сессий (для FastAPI)
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def init_db() -> None:
    """Инициализация базы данных (создание таблиц)"""
    Base.metadata.create_all(bind=engine)
    print("База данных инициализирована")


def drop_db() -> None:
    """Удаление всех таблиц (для тестов)"""
    Base.metadata.drop_all(bind=engine)
    print("База данных очищена")


@contextmanager
def get_sync_session() -> Generator:
    """Контекстный менеджер для синхронных сессий"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Асинхронная зависимость для FastAPI"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_session() -> AsyncSession:
    """Альтернативное имя для обратной совместимости"""
    async for session in get_async_session():
        return session
    raise RuntimeError("Failed to get DB session")


# Экспорт моделей для удобного импорта
from app.models.session import Session
from app.models.user import User
from app.models.vault_item import VaultItem

__all__ = [
    "engine",
    "async_engine",
    "SessionLocal",
    "AsyncSessionLocal",
    "init_db",
    "drop_db",
    "get_sync_session",
    "get_async_session",
    "get_db_session",
    "User",
    "Session",
    "VaultItem",
]