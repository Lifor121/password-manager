"""
Конфигурация тестов и фикстуры.
"""
import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.user import User


# Тестовая база данных (SQLite в памяти для изоляции тестов)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Фикстура для event loop (необходима для pytest-asyncio)"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def async_engine():
    """Фикстура для асинхронного движка базы данных"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )
    
    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Удаляем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Фикстура для асинхронной сессии базы данных"""
    async_session = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
        
        # Откатываем изменения после теста
        await session.rollback()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Фикстура для тестового пользователя"""
    import uuid
    
    user = User(
        email=f"test.user.{uuid.uuid4().hex[:8]}@example.com",
        auth_hash="test_hash_123456789012345678901234567890123456789012345678901234567890",
        crypto_salt="test_salt_1234567890",
        encrypted_vault_key="test_encrypted_vault_key"
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest_asyncio.fixture
async def test_session(db_session: AsyncSession, test_user: User):
    """Фикстура для тестовой сессии"""
    from datetime import datetime, timedelta
    from app.models.session import Session
    
    session = Session(
        user_id=test_user.id,
        device_info="Test Device",
        expires_at=datetime.utcnow() + timedelta(hours=12)
    )
    
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    
    return session


@pytest_asyncio.fixture
async def test_vault_item(db_session: AsyncSession, test_user: User):
    """Фикстура для тестового элемента хранилища"""
    from app.models.vault_item import VaultItem
    
    vault_item = VaultItem(
        user_id=test_user.id,
        encrypted_title="encrypted_test_title",
        title_blind_index="test_blind_index",
        encrypted_login="encrypted_test_login",
        encrypted_password="encrypted_test_password",
        encrypted_url="encrypted_test_url",
        encrypted_comment="encrypted_test_comment"
    )
    
    db_session.add(vault_item)
    await db_session.commit()
    await db_session.refresh(vault_item)
    
    return vault_item


# Фабрики для создания тестовых данных
@pytest.fixture
def user_factory():
    """Фабрика для создания пользователей"""
    def create_user(**kwargs):
        defaults = {
            "email": f"user_{uuid.uuid4().hex[:8]}@example.com",
            "auth_hash": f"hash_{uuid.uuid4().hex[:64]}",
            "crypto_salt": f"salt_{uuid.uuid4().hex[:16]}",
            "encrypted_vault_key": f"key_{uuid.uuid4().hex[:32]}",
        }
        defaults.update(kwargs)
        return User(**defaults)
    return create_user


@pytest.fixture
def session_factory():
    """Фабрика для создания сессий"""
    def create_session(user_id: str, **kwargs):
        from datetime import datetime, timedelta
        
        defaults = {
            "user_id": user_id,
            "device_info": "Test Device",
            "expires_at": datetime.utcnow() + timedelta(hours=12),
        }
        defaults.update(kwargs)
        
        from app.models.session import Session
        return Session(**defaults)
    return create_session


@pytest.fixture
def vault_item_factory():
    """Фабрика для создания элементов хранилища"""
    def create_vault_item(user_id: str, **kwargs):
        import uuid
        
        defaults = {
            "user_id": user_id,
            "encrypted_title": f"encrypted_title_{uuid.uuid4().hex[:8]}",
            "title_blind_index": f"index_{uuid.uuid4().hex[:16]}",
            "encrypted_login": f"encrypted_login_{uuid.uuid4().hex[:8]}",
            "encrypted_password": f"encrypted_password_{uuid.uuid4().hex[:16]}",
        }
        defaults.update(kwargs)
        
        from app.models.vault_item import VaultItem
        return VaultItem(**defaults)
    return create_vault_item