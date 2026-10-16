import base64
from collections.abc import AsyncGenerator
import uuid

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import get_async_session
from app.core.rate_limit import limiter
from app.main import app
from app.models.base import Base

# Асинхронная in-memory SQLite база для изолированных тестов
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

def _b64(text: str) -> str:
    """Хелпер для кодирования тестовых строк в валидный base64."""
    return base64.b64encode(text.encode("utf-8")).decode("ascii")

@pytest.fixture()
def client():
    """Фикстура: пересоздаёт таблицы перед каждым тестом и подменяет БД."""
    import asyncio

    async def init_models() -> None:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_models() -> None:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    asyncio.run(init_models())

    async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
        async with TestingSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_async_session] = override_get_async_session
    # Отключаем rate limiter во время обычных функциональных тестов
    limiter.enabled = False

    with TestClient(app) as test_client:
        yield test_client

    limiter.enabled = True
    app.dependency_overrides.clear()
    asyncio.run(drop_models())

# --- Вспомогательные данные и функции ---

USER_DATA = {
    "email": "TestUser@Example.com",
    "master_password_hash": "a" * 64,
    "encrypted_vault_key": _b64("encrypted-vault-key-123456"),
    "crypto_salt": _b64("random-salt-1234"),
}

def register_and_login(client: TestClient, email: str = USER_DATA["email"]) -> dict[str, str]:
    """Регистрирует и логинит пользователя, возвращает заголовки Authorization."""
    reg_payload = {**USER_DATA, "email": email}
    r_reg = client.post("/api/auth/register", json=reg_payload)
    assert r_reg.status_code == 201, r_reg.text

    r_login = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "master_password_hash": USER_DATA["master_password_hash"],
        },
        headers={"User-Agent": "PytestAgent/1.0"},
    )
    assert r_login.status_code == 200, r_login.text
    token = r_login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# =====================================================================
# 1. Тесты /api/auth
# =====================================================================

def test_register_and_duplicate_conflict(client: TestClient) -> None:
    """POST /api/auth/register: 201 при успехе и 409 при дубликате email."""
    res1 = client.post("/api/auth/register", json=USER_DATA)
    assert res1.status_code == 201

    # Повторная регистрация того же email (даже в другом регистре) -> 409
    res2 = client.post(
        "/api/auth/register",
        json={**USER_DATA, "email": "testuser@example.com"},
    )
    assert res2.status_code == 409

def test_get_auth_params(client: TestClient) -> None:
    """GET /api/auth/params: возвращает реальную соль для юзера и фейковую для чужого."""
    client.post("/api/auth/register", json=USER_DATA)

    # Существующий пользователь
    res_real = client.get("/api/auth/params", params={"email": "testuser@example.com"})
    assert res_real.status_code == 200
    assert res_real.json()["crypto_salt"] == USER_DATA["crypto_salt"]

    # Несуществующий пользователь (защита от User Enumeration: 200 + детерминированная соль)
    res_fake1 = client.get("/api/auth/params", params={"email": "nobody@example.com"})
    res_fake2 = client.get("/api/auth/params", params={"email": "nobody@example.com"})
    assert res_fake1.status_code == 200
    assert res_fake1.json()["crypto_salt"] == res_fake2.json()["crypto_salt"]
    assert res_fake1.json()["crypto_salt"] != USER_DATA["crypto_salt"]

def test_login_success_and_wrong_password(client: TestClient) -> None:
    """POST /api/auth/login: 200 с токеном/ключами при успехе, 401 при неверном хеше."""
    client.post("/api/auth/register", json=USER_DATA)

    # Неверный пароль -> 401
    res_bad = client.post(
        "/api/auth/login",
        json={"email": USER_DATA["email"], "master_password_hash": "b" * 64},
    )
    assert res_bad.status_code == 401

    # Верный пароль -> 200
    res_ok = client.post(
        "/api/auth/login",
        json={
            "email": USER_DATA["email"],
            "master_password_hash": USER_DATA["master_password_hash"],
        },
    )
    assert res_ok.status_code == 200
    body = res_ok.json()
    assert uuid.UUID(body["access_token"])
    assert body["encrypted_vault_key"] == USER_DATA["encrypted_vault_key"]
    assert body["crypto_salt"] == USER_DATA["crypto_salt"]

def test_logout_revokes_session(client: TestClient) -> None:
    """POST /api/auth/logout: отзывает текущую сессию, после чего запросы дают 401."""
    headers = register_and_login(client)

    res_logout = client.post("/api/auth/logout", headers=headers)
    assert res_logout.status_code == 200

    # Попытка обратиться к хранилищу с отозванной сессией -> 401
    res_vault = client.get("/api/vault/items", headers=headers)
    assert res_vault.status_code == 401

# =====================================================================
# 2. Тесты /api/vault
# =====================================================================

def test_vault_crud_and_isolation(client: TestClient) -> None:
    """Полный цикл CRUD для /api/vault/items + проверка изоляции между юзерами."""
    headers_user1 = register_and_login(client, email="user1@example.com")
    headers_user2 = register_and_login(client, email="user2@example.com")

    # 1. Создание карточки (POST /api/vault/items)
    create_payload = {
        "encrypted_title": _b64("GitHub"),
        "encrypted_password": _b64("secret_pass_1"),
        "encrypted_login": _b64("user1_login"),
        "encrypted_url": _b64("https://github.com"),
        "encrypted_comment": _b64("work account"),
        "title_blind_index": "0123456789abcdef0123456789abcdef",
    }
    r_create = client.post("/api/vault/items", json=create_payload, headers=headers_user1)
    assert r_create.status_code == 201, r_create.text
    created_item = r_create.json()
    item_id = created_item["id"]
    assert created_item["encrypted_title"] == create_payload["encrypted_title"]

    # 2. Получение списка (GET /api/vault/items)
    r_list = client.get("/api/vault/items", headers=headers_user1)
    assert r_list.status_code == 200
    assert r_list.json()["total"] == 1
    assert r_list.json()["items"][0]["id"] == item_id

    # У второго пользователя список должен быть пустым
    r_list_user2 = client.get("/api/vault/items", headers=headers_user2)
    assert r_list_user2.status_code == 200
    assert r_list_user2.json()["total"] == 0

    # 3. Получение по ID (GET /api/vault/items/{id})
    r_get = client.get(f"/api/vault/items/{item_id}", headers=headers_user1)
    assert r_get.status_code == 200
    assert r_get.json()["id"] == item_id

    # Попытка user2 получить чужую карточку -> 404 (не 403 по спецификации!)
    r_get_foreign = client.get(f"/api/vault/items/{item_id}", headers=headers_user2)
    assert r_get_foreign.status_code == 404

    # 4. Обновление карточки (PUT /api/vault/items/{id})
    update_payload = {
        "encrypted_title": _b64("GitLab"),
        "encrypted_password": _b64("new_secret_pass"),
    }
    r_put = client.put(f"/api/vault/items/{item_id}", json=update_payload, headers=headers_user1)
    assert r_put.status_code == 200
    assert r_put.json()["encrypted_title"] == update_payload["encrypted_title"]

    # 5. Удаление карточки (DELETE /api/vault/items/{id})
    r_del_foreign = client.delete(f"/api/vault/items/{item_id}", headers=headers_user2)
    assert r_del_foreign.status_code == 404

    r_del = client.delete(f"/api/vault/items/{item_id}", headers=headers_user1)
    assert r_del.status_code == 204

    # Проверка, что карточка удалена
    r_get_after = client.get(f"/api/vault/items/{item_id}", headers=headers_user1)
    assert r_get_after.status_code == 404

# =====================================================================
# 3. Тесты /api/users
# =====================================================================

def test_change_password_revokes_other_sessions(client: TestClient) -> None:
    """PUT /api/users/me/password: меняет хеш и отзывает все сессии, кроме текущей."""
    headers_session1 = register_and_login(client)

    # Вторая сессия того же пользователя (например, с другого устройства)
    r_login2 = client.post(
        "/api/auth/login",
        json={
            "email": USER_DATA["email"],
            "master_password_hash": USER_DATA["master_password_hash"],
        },
    )
    headers_session2 = {"Authorization": f"Bearer {r_login2.json()['access_token']}"}

    # Неверный старый пароль -> 400
    r_bad = client.put(
        "/api/users/me/password",
        json={
            "old_password_hash": "wrong" * 10,
            "new_password_hash": "c" * 64,
            "new_encrypted_vault_key": _b64("new-vault-key-123456"),
        },
        headers=headers_session1,
    )
    assert r_bad.status_code == 400

    # Успешная смена пароля с сессии 1
    new_hash = "c" * 64
    new_key = _b64("new-vault-key-123456")
    r_ok = client.put(
        "/api/users/me/password",
        json={
            "old_password_hash": USER_DATA["master_password_hash"],
            "new_password_hash": new_hash,
            "new_encrypted_vault_key": new_key,
        },
        headers=headers_session1,
    )
    assert r_ok.status_code == 200

    # Сессия 1 продолжает работать
    assert client.get("/api/vault/items", headers=headers_session1).status_code == 200
    # Сессия 2 должна быть отозвана -> 401
    assert client.get("/api/vault/items", headers=headers_session2).status_code == 401

    # Вход со старым паролем больше не работает -> 401
    assert (
        client.post(
            "/api/auth/login",
            json={"email": USER_DATA["email"], "master_password_hash": USER_DATA["master_password_hash"]},
        ).status_code
        == 401
    )
    # Вход с новым паролем успешен -> 200 и возвращает новый ключ
    r_new_login = client.post(
        "/api/auth/login",
        json={"email": USER_DATA["email"], "master_password_hash": new_hash},
    )
    assert r_new_login.status_code == 200
    assert r_new_login.json()["encrypted_vault_key"] == new_key

def test_delete_account_cascades(client: TestClient) -> None:
    """DELETE /api/users/me: возвращает 204 и удаляет аккаунт со всеми сессиями и карточками."""
    headers = register_and_login(client)

    # Создаём карточку
    client.post(
        "/api/vault/items",
        json={"encrypted_title": _b64("Title"), "encrypted_password": _b64("Pass")},
        headers=headers,
    )

    # Удаляем аккаунт
    r_del = client.delete("/api/users/me", headers=headers)
    assert r_del.status_code == 204

    # Сессия больше недействительна -> 401
    assert client.get("/api/vault/items", headers=headers).status_code == 401

    # Повторная регистрация того же email снова доступна -> 201
    r_re_reg = client.post("/api/auth/register", json=USER_DATA)
    assert r_re_reg.status_code == 201
