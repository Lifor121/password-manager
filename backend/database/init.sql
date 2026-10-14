-- Инициализация базы данных для менеджера паролей
-- Zero-Knowledge архитектура, PostgreSQL

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    auth_hash VARCHAR(255) NOT NULL, -- master_password_hash в hex формате
    crypto_salt VARCHAR(255) NOT NULL,
    encrypted_vault_key TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Таблица сессий
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_info VARCHAR(255),
    is_revoked BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Таблица элементов хранилища (паролей)
CREATE TABLE IF NOT EXISTS vault_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    encrypted_title TEXT NOT NULL,
    title_blind_index VARCHAR(255) NOT NULL,
    encrypted_login TEXT NOT NULL,
    encrypted_password TEXT NOT NULL,
    encrypted_url TEXT,
    encrypted_comment TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_is_revoked ON sessions(is_revoked);
CREATE INDEX IF NOT EXISTS idx_vault_items_user_id ON vault_items(user_id);
CREATE INDEX IF NOT EXISTS idx_vault_items_title_blind_index ON vault_items(title_blind_index);

-- Комментарии к таблицам для документации
COMMENT ON TABLE users IS 'Таблица пользователей с Zero-Knowledge аутентификацией';
COMMENT ON TABLE sessions IS 'Таблица сессий для Bearer-токенов аутентификации';
COMMENT ON TABLE vault_items IS 'Таблица зашифрованных паролей пользователей';

-- Комментарии к полям
COMMENT ON COLUMN users.auth_hash IS 'Хэш мастер-пароля (KDF на клиенте)';
COMMENT ON COLUMN users.crypto_salt IS 'Соль для криптографических операций';
COMMENT ON COLUMN users.encrypted_vault_key IS 'Зашифрованный симметричный ключ хранилища';
COMMENT ON COLUMN sessions.device_info IS 'Информация об устройстве (обрезается до 255 символов)';
COMMENT ON COLUMN sessions.is_revoked IS 'Флаг отзыва сессии';
COMMENT ON COLUMN sessions.expires_at IS 'Время истечения сессии (TTL 12 часов)';
COMMENT ON COLUMN vault_items.title_blind_index IS 'Слепой индекс для поиска по названию сервиса';
COMMENT ON COLUMN vault_items.encrypted_title IS 'Зашифрованное название сервиса';
COMMENT ON COLUMN vault_items.encrypted_login IS 'Зашифрованный логин';
COMMENT ON COLUMN vault_items.encrypted_password IS 'Зашифрованный пароль';
COMMENT ON COLUMN vault_items.encrypted_url IS 'Зашифрованный URL';
COMMENT ON COLUMN vault_items.encrypted_comment IS 'Зашифрованный комментарий';