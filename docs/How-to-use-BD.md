# Руководство по использованию базы данных менеджера паролей

## Содержание
1. [Архитектурный обзор](#архитектурный-обзор)
2. [Структура проекта](#структура-проекта)
3. [Настройка окружения](#настройка-окружения)
4. [Инициализация базы данных](#инициализация-базы-данных)
5. [Работа с миграциями](#работа-с-миграциями)
6. [Тестирование системы](#тестирование-системы)
7. [Запуск приложения](#запуск-приложения)
8. [Резервное копирование и восстановление](#резервное-копирование-и-восстановление)

---

## Архитектурный обзор

### Zero-Knowledge принципы
Менеджер паролей построен на принципах Zero-Knowledge архитектуры:
- **Мастер-пароль** никогда не передается на сервер
- Все **шифрование** выполняется на стороне клиента
- Сервер хранит только **хэши** и **зашифрованные данные**
- **Bearer-токены** представлены в виде UUID сессий из таблицы `sessions`

### Модели данных
Система использует три основные таблицы:

#### Таблица `users`
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    auth_hash VARCHAR(255) NOT NULL, -- master_password_hash в hex формате
    crypto_salt VARCHAR(255) NOT NULL, -- Соль для криптографических операций
    encrypted_vault_key TEXT NOT NULL, -- Зашифрованный симметричный ключ хранилища
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

#### Таблица `sessions`
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_info VARCHAR(255), -- Информация об устройстве (обрезается до 255 символов)
    is_revoked BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMPTZ NOT NULL, -- TTL 12 часов
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

#### Таблица `vault_items`
```sql
CREATE TABLE vault_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    encrypted_title TEXT NOT NULL,
    title_blind_index VARCHAR(255) NOT NULL, -- Слепой индекс для поиска
    encrypted_login TEXT NOT NULL,
    encrypted_password TEXT NOT NULL,
    encrypted_url TEXT,
    encrypted_comment TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

---

## Структура проекта

### Директория `backend/app/models/`
- **Назначение**: Определение структуры данных в PostgreSQL через SQLAlchemy ORM
- **Содержимое**:
  - `base.py` - базовые миксины (TimestampMixin, UUIDMixin)
  - `user.py` - модель пользователя с Zero-Knowledge аутентификацией
  - `session.py` - модель сессии для Bearer-токенов
  - `vault_item.py` - модель зашифрованного элемента хранилища

### Директория `backend/app/schemas/`
- **Назначение**: Валидация запросов и ответов API через Pydantic
- **Содержимое**:
  - `auth.py` - схемы аутентификации (RegisterRequest, LoginRequest, LoginResponse, ChangePasswordRequest)
  - `vault.py` - схемы операций с хранилищем

### Директория `backend/database/`
- **Назначение**: SQL скрипты для развертывания и управления базой данных
- **Содержимое**:
  - `init.sql` - создание таблиц и индексов
  - `update.sql` - обновления схемы базы данных
  - `test_data.sql` - тестовые данные для разработки

### Директория `backend/alembic/`
- **Назначение**: Управление версиями схемы базы данных
- **Содержимое**:
  - `versions/001_initial_tables.py` - первая миграция
  - `env.py` - конфигурация Alembic

---

## Настройка окружения

### Предварительные требования
1. **Python 3.11+**
2. **PostgreSQL 14+**
3. **Установленные зависимости Python**

### Установка зависимостей
```bash
# Переход в директорию backend
cd backend

# Активация виртуального окружения
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Установка основных зависимостей
pip install -r requirements.txt

# Установка зависимостей для разработки
pip install -r requirements-dev.txt
```

### Настройка PostgreSQL
```bash
# Создание базы данных
createdb password_manager

# Создание пользователя (пример)
psql -c "CREATE USER password_user WITH PASSWORD 'secure_password';"

# Назначение прав
psql -c "GRANT ALL PRIVILEGES ON DATABASE password_manager TO password_user;"
```

### Конфигурация приложения
```bash
# Копирование примера конфигурации
cp .env.example .env

# Редактирование файла .env
# Установите следующие значения:
DATABASE_URL=postgresql://password_user:secure_password@localhost/password_manager
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_ECHO=false
```

---

## Инициализация базы данных

### Метод 1: Использование Alembic (рекомендуется)
```bash
# Применение всех миграций
alembic upgrade head

# Проверка текущего состояния
alembic current

# Просмотр истории миграций
alembic history
```

### Метод 2: Использование скрипта инициализации
```bash
# Запуск скрипта инициализации
python init_db.py
```

### Метод 3: Непосредственное выполнение SQL скрипта
```bash
# Выполнение init.sql через psql
psql -U password_user -d password_manager -f database/init.sql

# Загрузка тестовых данных (опционально)
psql -U password_user -d password_manager -f database/test_data.sql
```

### Проверка подключения
```python
# Python скрипт для проверки подключения
from app.core.database import engine, init_db

# Проверка подключения
print("Проверка подключения к базе данных...")
try:
    with engine.connect() as connection:
        print("✅ Подключение к PostgreSQL успешно установлено")
except Exception as e:
    print(f"❌ Ошибка подключения: {e}")

# Инициализация базы данных (создание таблиц)
init_db()
```

---

## Работа с миграциями

### Создание новой миграции
```bash
# Генерация миграции на основе изменений в моделях
alembic revision --autogenerate -m "Описание изменений"

# Пример: добавление нового поля
alembic revision --autogenerate -m "Add last_login field to users table"
```

### Применение миграций
```bash
# Применение всех миграций до последней
alembic upgrade head

# Применение конкретной миграции
alembic upgrade <revision_id>

# Откат последней миграции
alembic downgrade -1

# Откат к конкретной версии
alembic downgrade <revision_id>
```

### Просмотр состояния миграций
```bash
# Текущая примененная миграция
alembic current

# Все миграции
alembic history

# Непримененные миграции
alembic heads
```

---

## Тестирование системы

### Запуск всех тестов
```bash
# Запуск тестов с покрытием
pytest --cov=app tests/

# Запуск тестов с подробным выводом
pytest -v tests/

# Запуск конкретного тестового файла
pytest tests/test_models.py
```

### Тестирование моделей
```bash
# Тестирование работы моделей
pytest tests/test_models.py -v

# Тестирование схем валидации
pytest tests/test_schemas.py -v
```

### Проверка работы SQLAlchemy моделей
```python
# Пример проверки работы моделей
from app.core.database import get_sync_session
from app.models.user import User

with get_sync_session() as session:
    # Проверка создания пользователя
    user = User(
        email="test@example.com",
        auth_hash="test_hash_123",
        crypto_salt="test_salt_123",
        encrypted_vault_key="test_key_123"
    )
    session.add(user)
    session.commit()
    
    # Проверка поиска пользователя
    found_user = session.query(User).filter_by(email="test@example.com").first()
    print(f"Найден пользователь: {found_user}")
```

---

## Запуск приложения

### Разработческий режим
```bash
# Запуск сервера FastAPI с автоматической перезагрузкой
uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
```

### Продукционный режим
```bash
# Использование Gunicorn для продакшн-окружения
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Использование Makefile (если доступен)
```bash
# Установка и запуск
make setup
make dev

# Тестирование
make test
make lint

# Очистка
make clean
```

### Проверка работоспособности API
```bash
# После запуска сервера проверьте:
curl http://localhost:8000/docs  # Документация OpenAPI
curl http://localhost:8000/redoc  # Альтернативная документация
curl http://localhost:8000/health  # Проверка здоровья (если реализовано)
```

---

## Резервное копирование и восстановление

### Экспорт данных
```bash
# Экспорт структуры базы данных
pg_dump -U password_user -d password_manager --schema-only > backup_schema.sql

# Экспорт данных
pg_dump -U password_user -d password_manager --data-only > backup_data.sql

# Полный экспорт
pg_dump -U password_user -d password_manager > full_backup.sql
```

### Импорт данных
```bash
# Восстановление из полного бэкапа
psql -U password_user -d password_manager < full_backup.sql

# Восстановление только структуры
psql -U password_user -d password_manager < backup_schema.sql
```

### Автоматическое резервное копирование
```bash
# Пример скрипта для автоматического бэкапа
#!/bin/bash
BACKUP_DIR="/var/backups/password_manager"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql"

pg_dump -U password_user -d password_manager > $BACKUP_FILE

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "backup_*.sql" -mtime +30 -delete
```

---

## Мониторинг и обслуживание

### Проверка состояния базы данных
```bash
# Проверка размера базы данных
psql -U password_user -d password_manager -c "SELECT pg_size_pretty(pg_database_size('password_manager'));"

# Проверка размера таблиц
psql -U password_user -d password_manager -c "
SELECT 
    table_name,
    pg_size_pretty(pg_total_relation_size('\"' || table_name || '\"')) as total_size
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY pg_total_relation_size('\"' || table_name || '\"') DESC;
"

# Проверка активности соединений
psql -U password_user -d password_manager -c "SELECT * FROM pg_stat_activity;"
```

### Оптимизация производительности
```bash
# Перестройка индексов
psql -U password_user -d password_manager -c "REINDEX DATABASE password_manager;"

# Сбор статистики
psql -U password_user -d password_manager -c "VACUUM ANALYZE;"
```

---

## Устранение неполадок

### Распространенные проблемы и решения

#### Проблема: Не удается подключиться к PostgreSQL
**Решение:**
1. Проверьте, запущен ли сервер PostgreSQL: `systemctl status postgresql` (Linux) или `services.msc` (Windows)
2. Проверьте настройки аутентификации в `pg_hba.conf`
3. Проверьте правильность параметров подключения в `.env`

#### Проблема: Ошибки миграции Alembic
**Решение:**
```bash
# Сброс миграций (осторожно!)
alembic downgrade base

# Повторное применение миграций
alembic upgrade head
```

#### Проблема: Медленные запросы
**Решение:**
1. Проверьте индексы: `psql -c "\di"`
2. Проверьте план выполнения запросов с `EXPLAIN ANALYZE`
3. Рассмотрите добавление недостающих индексов

---

## Дополнительные ресурсы

### Документация
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

### Полезные команды
```bash
# Просмотр логов PostgreSQL
tail -f /var/log/postgresql/postgresql-14-main.log

# Мониторинг в реальном времени
pg_top  # Требуется установка дополнительного ПО

# Проверка блокировок
psql -c "SELECT * FROM pg_locks WHERE granted = false;"
```

---

## Контакты и поддержка

Для получения дополнительной помощи:
1. Обратитесь к документации проекта в `/docs/`
2. Проверьте примеры использования в тестах `/backend/tests/`

---

*Последнее обновление: 13 октября 2026*