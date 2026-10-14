-- Тестовые данные для разработки
-- ВНИМАНИЕ: Этот скрипт только для тестовой среды!

-- Очистка существующих данных
TRUNCATE TABLE vault_items CASCADE;
TRUNCATE TABLE sessions CASCADE;
TRUNCATE TABLE users CASCADE;

-- Тестовые пользователи
INSERT INTO users (id, email, auth_hash, crypto_salt, encrypted_vault_key) VALUES
(
    '11111111-1111-1111-1111-111111111111',
    'test@example.com',
    'a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890', -- PBKDF2-SHA256 hex 64
    'salt1234567890',
    'encrypted_vault_key_for_test_user_1'
),
(
    '22222222-2222-2222-2222-222222222222',
    'user2@example.com',
    'f0e1d2c3b4a5968778695847362514039281726354453627182910000000000',
    'salt9876543210',
    'encrypted_vault_key_for_test_user_2'
);

-- Тестовые сессии
INSERT INTO sessions (id, user_id, device_info, is_revoked, expires_at) VALUES
(
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    '11111111-1111-1111-1111-111111111111',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    FALSE,
    CURRENT_TIMESTAMP + INTERVAL '12 hours'
),
(
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    '11111111-1111-1111-1111-111111111111',
    'Mobile Safari',
    FALSE,
    CURRENT_TIMESTAMP + INTERVAL '6 hours'
),
(
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    '22222222-2222-2222-2222-222222222222',
    'Postman Runtime',
    TRUE, -- отозвана
    CURRENT_TIMESTAMP + INTERVAL '1 hour'
);

-- Тестовые записи хранилища
INSERT INTO vault_items (id, user_id, encrypted_title, title_blind_index, encrypted_login, encrypted_password, encrypted_url, encrypted_comment) VALUES
(
    'dddddddd-dddd-dddd-dddd-dddddddddddd',
    '11111111-1111-1111-1111-111111111111',
    'encrypted_google_title',
    'google_com_hash',
    'encrypted_user@gmail.com',
    'encrypted_password123',
    'encrypted_https://google.com',
    'encrypted_primary_account'
),
(
    'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
    '11111111-1111-1111-1111-111111111111',
    'encrypted_github_title',
    'github_com_hash',
    'encrypted_developer@github.com',
    'encrypted_github_token',
    'encrypted_https://github.com',
    'encrypted_work_account'
),
(
    'ffffffff-ffff-ffff-ffff-ffffffffffff',
    '22222222-2222-2222-2222-222222222222',
    'encrypted_bank_title',
    'bank_com_hash',
    'encrypted_client@bank.com',
    'encrypted_bank_password',
    'encrypted_https://bank.com',
    'encrypted_financial_account'
);

-- Проверка данных
SELECT 
    'Users count' as table_name,
    COUNT(*) as count
FROM users
UNION ALL
SELECT 
    'Sessions count',
    COUNT(*)
FROM sessions
UNION ALL
SELECT 
    'Active sessions',
    COUNT(*)
FROM sessions 
WHERE is_revoked = FALSE AND expires_at > CURRENT_TIMESTAMP
UNION ALL
SELECT 
    'Vault items count',
    COUNT(*)
FROM vault_items;