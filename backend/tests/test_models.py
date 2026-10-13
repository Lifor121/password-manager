"""
Тесты для моделей базы данных.
"""
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.session import Session
from app.models.vault_item import VaultItem


class TestUserModel:
    """Тесты для модели User"""
    
    @pytest.mark.asyncio
    async def test_create_user(self, db_session: AsyncSession):
        """Тест создания пользователя"""
        user = User(
            email="test@example.com",
            auth_hash="a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890",
            crypto_salt="salt1234567890",
            encrypted_vault_key="encrypted_vault_key_for_test"
        )
        
        db_session.add(user)
        await db_session.commit()
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.auth_hash.startswith("a1b2c3d4")
        assert user.crypto_salt == "salt1234567890"
        assert user.encrypted_vault_key == "encrypted_vault_key_for_test"
        assert user.created_at is not None
        assert user.updated_at is not None
        
        # Проверка свойств
        assert user.is_active is True
        
        # Проверка проверки пароля
        assert user.check_password_hash(user.auth_hash) is True
        assert user.check_password_hash("wrong_hash") is False
    
    @pytest.mark.asyncio
    async def test_user_update_password(self, db_session: AsyncSession):
        """Тест обновления пароля пользователя"""
        user = User(
            email="update@example.com",
            auth_hash="old_hash",
            crypto_salt="salt",
            encrypted_vault_key="old_key"
        )
        
        db_session.add(user)
        await db_session.commit()
        
        old_updated_at = user.updated_at
        
        # Обновляем пароль
        user.update_password("new_hash", "new_key")
        await db_session.commit()
        
        assert user.auth_hash == "new_hash"
        assert user.encrypted_vault_key == "new_key"
        assert user.updated_at > old_updated_at
    
    @pytest.mark.asyncio
    async def test_user_repr(self, db_session: AsyncSession):
        """Тест строкового представления пользователя"""
        user = User(
            email="repr@example.com",
            auth_hash="hash",
            crypto_salt="salt",
            encrypted_vault_key="key"
        )
        
        db_session.add(user)
        await db_session.commit()
        
        repr_str = repr(user)
        assert "User" in repr_str
        assert user.id in repr_str
        assert user.email in repr_str


class TestSessionModel:
    """Тесты для модели Session"""
    
    @pytest.mark.asyncio
    async def test_create_session(self, db_session: AsyncSession, test_user: User):
        """Тест создания сессии"""
        session = Session(
            user_id=test_user.id,
            device_info="Test Device Info",
            expires_at=datetime.utcnow() + timedelta(hours=12)
        )
        
        db_session.add(session)
        await db_session.commit()
        
        assert session.id is not None
        assert session.user_id == test_user.id
        assert session.device_info == "Test Device Info"
        assert session.is_revoked is False
        assert session.expires_at > datetime.utcnow()
        assert session.created_at is not None
    
    @pytest.mark.asyncio
    async def test_session_factory_method(self, db_session: AsyncSession, test_user: User):
        """Тест фабричного метода создания сессии"""
        session = Session.create_session(
            user_id=test_user.id,
            device_info="Mozilla/5.0 (Windows NT 10.0; Win64; x64) " + "A" * 300,  # Длинный device_info
            ttl_hours=24
        )
        
        # Проверка обрезки длинного device_info
        assert len(session.device_info) <= 255
        assert session.device_info.startswith("Mozilla/5.0")
        
        # Проверка TTL
        expected_expiry = datetime.utcnow() + timedelta(hours=24)
        time_diff = abs((session.expires_at - expected_expiry).total_seconds())
        assert time_diff < 10  # Разница меньше 10 секунд
    
    @pytest.mark.asyncio
    async def test_session_validity(self, db_session: AsyncSession, test_user: User):
        """Тест проверки валидности сессии"""
        # Активная сессия
        active_session = Session(
            user_id=test_user.id,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        assert active_session.is_valid is True
        
        # Отозванная сессия
        revoked_session = Session(
            user_id=test_user.id,
            is_revoked=True,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        assert revoked_session.is_valid is False
        
        # Истекшая сессия
        expired_session = Session(
            user_id=test_user.id,
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        assert expired_session.is_valid is False
    
    @pytest.mark.asyncio
    async def test_session_revoke(self, db_session: AsyncSession, test_user: User):
        """Тест отзыва сессии"""
        session = Session(
            user_id=test_user.id,
            expires_at=datetime.utcnow() + timedelta(hours=12)
        )
        
        # Добавляем и сохраняем сессию, чтобы получить id
        db_session.add(session)
        await db_session.commit()
        
        assert session.is_revoked is False
        session.revoke()
        assert session.is_revoked is True
    
    @pytest.mark.asyncio
    async def test_session_renew(self, db_session: AsyncSession, test_user: User):
        """Тест продления сессии"""
        session = Session(
            user_id=test_user.id,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        old_expires_at = session.expires_at
        session.renew(ttl_hours=24)
        
        assert session.expires_at > old_expires_at
        assert session.time_remaining() > timedelta(hours=23)
    
    @pytest.mark.asyncio
    async def test_session_repr(self, db_session: AsyncSession, test_user: User):
        """Тест строкового представления сессии"""
        session = Session(
            user_id=test_user.id,
            expires_at=datetime.utcnow() + timedelta(hours=12)
        )
        
        # Добавляем и сохраняем сессию, чтобы получить id
        db_session.add(session)
        await db_session.commit()
        
        repr_str = repr(session)
        assert "Session" in repr_str
        assert str(session.id) in repr_str
        assert test_user.id in repr_str


class TestVaultItemModel:
    """Тесты для модели VaultItem"""
    
    @pytest.mark.asyncio
    async def test_create_vault_item(self, db_session: AsyncSession, test_user: User):
        """Тест создания элемента хранилища"""
        vault_item = VaultItem(
            user_id=test_user.id,
            encrypted_title="encrypted_google_title",
            title_blind_index="google_com_hash",
            encrypted_login="encrypted_user@gmail.com",
            encrypted_password="encrypted_password123",
            encrypted_url="encrypted_https://google.com",
            encrypted_comment="encrypted_primary_account"
        )
        
        db_session.add(vault_item)
        await db_session.commit()
        
        assert vault_item.id is not None
        assert vault_item.user_id == test_user.id
        assert vault_item.encrypted_title == "encrypted_google_title"
        assert vault_item.title_blind_index == "google_com_hash"
        assert vault_item.encrypted_login == "encrypted_user@gmail.com"
        assert vault_item.encrypted_password == "encrypted_password123"
        assert vault_item.encrypted_url == "encrypted_https://google.com"
        assert vault_item.encrypted_comment == "encrypted_primary_account"
        assert vault_item.created_at is not None
        assert vault_item.updated_at is not None
        
        # Проверка свойств
        assert vault_item.has_url is True
        assert vault_item.has_comment is True
    
    @pytest.mark.asyncio
    async def test_vault_item_without_optional_fields(self, db_session: AsyncSession, test_user: User):
        """Тест создания элемента хранилища без опциональных полей"""
        vault_item = VaultItem(
            user_id=test_user.id,
            encrypted_title="encrypted_title",
            title_blind_index="blind_index",
            encrypted_login="encrypted_login",
            encrypted_password="encrypted_password"
        )
        
        db_session.add(vault_item)
        await db_session.commit()
        
        assert vault_item.encrypted_url is None
        assert vault_item.encrypted_comment is None
        assert vault_item.has_url is False
        assert vault_item.has_comment is False
    
    @pytest.mark.asyncio
    async def test_vault_item_update(self, db_session: AsyncSession, test_user: User):
        """Тест обновления элемента хранилища"""
        vault_item = VaultItem(
            user_id=test_user.id,
            encrypted_title="old_title",
            title_blind_index="old_index",
            encrypted_login="old_login",
            encrypted_password="old_password"
        )
        
        db_session.add(vault_item)
        await db_session.commit()
        
        old_updated_at = vault_item.updated_at
        
        # Обновляем данные
        vault_item.update_from_encrypted_data(
            encrypted_title="new_title",
            title_blind_index="new_index",
            encrypted_login="new_login",
            encrypted_password="new_password",
            encrypted_url="new_url",
            encrypted_comment="new_comment"
        )
        
        await db_session.commit()
        
        assert vault_item.encrypted_title == "new_title"
        assert vault_item.title_blind_index == "new_index"
        assert vault_item.encrypted_login == "new_login"
        assert vault_item.encrypted_password == "new_password"
        assert vault_item.encrypted_url == "new_url"
        assert vault_item.encrypted_comment == "new_comment"
        assert vault_item.updated_at > old_updated_at
    
    @pytest.mark.asyncio
    async def test_vault_item_to_dict(self, db_session: AsyncSession, test_user: User):
        """Тест преобразования в словарь"""
        vault_item = VaultItem(
            user_id=test_user.id,
            encrypted_title="encrypted_title",
            title_blind_index="blind_index",
            encrypted_login="encrypted_login",
            encrypted_password="encrypted_password",
            encrypted_url="encrypted_url",
            encrypted_comment="encrypted_comment"
        )
        
        db_session.add(vault_item)
        await db_session.commit()
        
        result = vault_item.to_dict()
        
        assert result["id"] == vault_item.id
        assert result["user_id"] == test_user.id
        assert result["encrypted_title"] == "encrypted_title"
        assert result["title_blind_index"] == "blind_index"
        assert result["encrypted_login"] == "encrypted_login"
        assert result["encrypted_password"] == "encrypted_password"
        assert result["encrypted_url"] == "encrypted_url"
        assert result["encrypted_comment"] == "encrypted_comment"
        assert "created_at" in result
        assert "updated_at" in result
    
    @pytest.mark.asyncio
    async def test_vault_item_repr(self, db_session: AsyncSession, test_user: User):
        """Тест строкового представления элемента хранилища"""
        vault_item = VaultItem(
            user_id=test_user.id,
            encrypted_title="encrypted_title",
            title_blind_index="very_long_blind_index_for_testing_purposes",
            encrypted_login="encrypted_login",
            encrypted_password="encrypted_password"
        )
        
        # Добавляем и сохраняем элемент хранилища, чтобы получить id
        db_session.add(vault_item)
        await db_session.commit()
        
        repr_str = repr(vault_item)
        assert "VaultItem" in repr_str
        assert str(vault_item.id) in repr_str
        assert test_user.id in repr_str
        assert "very_long" in repr_str  # Обрезанный blind_index (первые 10 символов из repr)


class TestModelRelationships:
    """Тесты для связей между моделями"""
    
    @pytest.mark.asyncio
    async def test_user_sessions_relationship(self, db_session: AsyncSession, test_user: User):
        """Тест связи пользователь-сессии"""
        # Создаем сессии для пользователя
        session1 = Session(
            user_id=test_user.id,
            expires_at=datetime.utcnow() + timedelta(hours=12)
        )
        session2 = Session(
            user_id=test_user.id,
            expires_at=datetime.utcnow() + timedelta(hours=6)
        )
        
        db_session.add_all([session1, session2])
        await db_session.commit()
        
        # Явно загружаем сессии для пользователя
        from sqlalchemy import select
        
        sessions_stmt = select(Session).where(Session.user_id == test_user.id)
        result = await db_session.execute(sessions_stmt)
        user_sessions = result.scalars().all()
        
        assert len(user_sessions) == 2
        assert session1 in user_sessions
        assert session2 in user_sessions
        assert user_sessions[0].user_id == test_user.id
    
    @pytest.mark.asyncio
    async def test_user_vault_items_relationship(self, db_session: AsyncSession, test_user: User):
        """Тест связи пользователь-элементы хранилища"""
        # Создаем элементы хранилища для пользователя
        item1 = VaultItem(
            user_id=test_user.id,
            encrypted_title="item1_title",
            title_blind_index="item1_index",
            encrypted_login="item1_login",
            encrypted_password="item1_password"
        )
        item2 = VaultItem(
            user_id=test_user.id,
            encrypted_title="item2_title",
            title_blind_index="item2_index",
            encrypted_login="item2_login",
            encrypted_password="item2_password"
        )
        
        db_session.add_all([item1, item2])
        await db_session.commit()
        
        # Явно загружаем элементы хранилища для пользователя
        from sqlalchemy import select
        
        items_stmt = select(VaultItem).where(VaultItem.user_id == test_user.id)
        result = await db_session.execute(items_stmt)
        user_items = result.scalars().all()
        
        assert len(user_items) == 2
        assert item1 in user_items
        assert item2 in user_items
        assert user_items[0].user_id == test_user.id
    
    @pytest.mark.asyncio
    async def test_cascade_delete(self, db_session: AsyncSession, test_user: User):
        """Тест каскадного удаления"""
        # Создаем связанные данные
        session = Session(
            user_id=test_user.id,
            expires_at=datetime.utcnow() + timedelta(hours=12)
        )
        vault_item = VaultItem(
            user_id=test_user.id,
            encrypted_title="title",
            title_blind_index="index",
            encrypted_login="login",
            encrypted_password="password"
        )
        
        db_session.add_all([session, vault_item])
        await db_session.commit()
        
        # Удаляем пользователя
        await db_session.delete(test_user)
        await db_session.commit()
        
        # Проверяем, что связанные данные тоже удалены
        session_result = await db_session.get(Session, session.id)
        vault_item_result = await db_session.get(VaultItem, vault_item.id)
        
        assert session_result is None
        assert vault_item_result is None