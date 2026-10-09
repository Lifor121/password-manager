# API Password Manager

## 1. Общее

- Base URL: `/api`; формат JSON (UTF-8).
- Идентификаторы: UUID v4.
- Даты: ISO 8601, UTC.
- Шифртексты: base64 (допустимы стандартный и url-safe алфавиты).
- Авторизация: `Authorization: Bearer <session_id>`, где session_id — UUID
  серверной сессии (НЕ JWT). 401 = сессии нет / отозвана / протухла,
  причина не раскрывается.
- Ошибки: единый формат `{"detail": "..."}`.
- Лимиты (429 + Retry-After): 120 req/min на IP — все запросы;
  30 req/min на сессию — пишущие vault-эндпоинты; 5 req/min на IP —
  auth (login/register/params).
- Максимальный размер тела запроса: 3 МБ → 413.

## 2. Zero-Knowledge модель

Сервер НИКОГДА не видит: мастер-пароль, логины/пароли/содержимое карточек.
Сервер хранит: email, auth_hash, crypto_salt, encrypted_vault_key, шифртексты.

Криптофлоу (клиент):
1. Регистрация: генерирует crypto_salt; из мастер-пароля + соли выводит
   auth_hash (KDF) и ключ шифрования; ключом шифрует vault_key.
2. Логин: GET /auth/params (получить соль) → считает auth_hash → POST /login.
3. Записи: шифруются vault_key (AES-GCM, свой nonce на каждое поле).

## 3. Авторизация /api/auth

POST /auth/register
  Body: email (≤254), master_password_hash (16–512), encrypted_vault_key
        (16–512), crypto_salt (8–512)
  → 201 | 409 email занят | 422

GET /auth/params?email=...
  → 200 {"crypto_salt": "..."}   [5 req/min на IP]

POST /auth/login
  Body: email, master_password_hash
  → 200 {"access_token": UUID, "encrypted_vault_key": "...", "crypto_salt": "..."}
  | 401
  Side-effect: создаётся строка в sessions (device_info, expires_at).

POST /auth/logout
  → 200. Отзывает текущую сессию (is_revoked = true).

## 4. Профиль /api/users

PUT /users/me/password
  Body: old_password_hash, new_password_hash, new_encrypted_vault_key
  → 200 | 400 неверный старый хеш
  Side-effect: отзываются все сессии, кроме текущей.
  ВАЖНО: записи хранилища НЕ перешифровываются (vault_key не меняется).

DELETE /users/me
  → 204. Каскадно удаляются все vault_items и sessions.

## 5. Хранилище /api/vault

Объект VaultItem:
  id: UUID
  encrypted_title: base64, обяз., ≤2048
  encrypted_password: base64, обяз., ≤4096
  encrypted_login / encrypted_url / encrypted_comment: base64, опц., ≤4096
  title_blind_index: hex 16–64, опц. — HMAC-SHA256(title, ключ из vault_key);
    нужен только для серверного поиска; ключа у сервера нет
  created_at / updated_at: ISO 8601

GET  /vault/items        → 200 {"items": [...], "total": n}
POST /vault/items        → 201 VaultItem        [30 req/min на сессию]
GET  /vault/items/{id}   → 200 | 404
PUT  /vault/items/{id}   → 200 (полная перезапись; тело как у POST)
DELETE /vault/items/{id} → 204

Поиск — на клиенте (локальная расшифровка). Серверный поиск через
title_blind_index — опциональное расширение, в v1 не включён.

## 6. Коды ошибок

400 — семантическая ошибка (напр., неверный старый пароль)
401 — сессия отсутствует/недействительна
404 — не найдено ИЛИ чужое (намеренно не 403 — не раскрываем существование)
409 — конфликт (email занят)
413 — тело больше 3 МБ
422 — валидация (детали Pydantic)
429 — rate limit (Retry-After)

## 7. Сессии

TTL 12 ч (предложение; финализирует владелец auth) с продлением при
активности. is_revoked — отзыв. device_info — User-Agent, обрезается до 255.

## 8. Зафиксированные решения

1. Раздельные зашифрованные поля, а не единый encrypted_data-блоб.
2. id везде UUID.
3. Bearer = UUID серверной сессии; JWT не используется.
4. crypto_salt передаётся при register и возвращается на login + /auth/params.
5. Поиск на клиенте.

## 9. Отложено

Пагинация GET /vault/items; серверный поиск по blind_index; экспорт в Excel;
refresh-механизм сессий.