-- Скрипт для обновления базы данных
-- Используется для внесения изменений в существующую структуру

-- Пример добавления нового поля (если понадобится)
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ;

-- Пример создания триггера для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггер для автоматического обновления updated_at в таблице users
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Триггер для автоматического обновления updated_at в таблице vault_items
DROP TRIGGER IF EXISTS update_vault_items_updated_at ON vault_items;
CREATE TRIGGER update_vault_items_updated_at
    BEFORE UPDATE ON vault_items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Индекс для поиска неотозванных сессий
CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(user_id) 
WHERE is_revoked = FALSE AND expires_at > CURRENT_TIMESTAMP;

-- Индекс для быстрого поиска сессий по токену
CREATE INDEX IF NOT EXISTS idx_sessions_id ON sessions(id);

-- Комментарий для будущих изменений
COMMENT ON TABLE users IS 'Таблица пользователей - может быть расширена для двухфакторной аутентификации';
COMMENT ON TABLE sessions IS 'Таблица сессий - может быть расширена для хранения IP адресов и геолокации';
COMMENT ON TABLE vault_items IS 'Таблица паролей - может быть расширена для категорий и тегов';