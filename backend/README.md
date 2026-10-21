# Backend менеджера паролей

Zero-Knowledge backend для менеджера паролей на FastAPI и PostgreSQL.

## Особенности

- **Zero-Knowledge архитектура**: Мастер-пароль никогда не передается на сервер
- **Bearer-токены как UUID сессии**: Безопасная аутентификация без JWT
- **Асинхронный FastAPI**: Высокая производительность
- **SQLAlchemy с asyncpg**: Асинхронная работа с PostgreSQL
- **Property-Based Testing**: Тестирование с использованием Hypothesis
- **Alembic миграции**: Управление схемой базы данных

## Быстрый старт

### Предварительные требования

1. Python 3.11+
2. PostgreSQL 14+
3. Git

### Установка

```bash
# Клонирование репозитория
git clone <repository-url>
cd password-manager/backend

# Установка зависимостей
make install

# Настройка окружения
cp .env.example .env
# Отредактируйте .env файл под ваше окружение

# Инициализация базы данных
make db-init

# Загрузка тестовых данных (опционально)
make db-test
```

### Запуск сервера

```bash
# Режим разработки
make dev

# Сервер будет доступен на http://localhost:8000
# Документация API: http://localhost:8000/docs
```

## Структура проекта

```
backend/
├── app/                      # Приложение FastAPI
│   ├── api/                 # API эндпоинты
│   ├── core/                # Основные настройки и утилиты
│   │   ├── config.py        # Конфигурация приложения
│   │   ├── database.py      # Подключение к базе данных
│   │   └── rate_limit.py    # Rate limiting
│   ├── models/              # Модели SQLAlchemy
│   │   ├── user.py          # Модель пользователя
│   │   ├── session.py       # Модель сессии
│   │   ├── vault_item.py    # Модель элемента хранилища
│   │   └── base.py          # Базовые классы моделей
│   ├── schemas/             # Pydantic схемы
│   ├── middleware/          # Middleware FastAPI
│   └── main.py              # Точка входа приложения
├── tests/                   # Тесты
│   ├── test_models.py       # Тесты моделей
│   ├── test_schemas.py      # Тесты схем
│   └── conftest.py          # Фикстуры pytest
├── database/                # SQL скрипты
│   ├── init.sql             # Инициализация базы данных
│   ├── update.sql           # Обновление структуры
│   ├── test_data.sql        # Тестовые данные
│   └── README.md            # Документация базы данных
├── alembic/                 # Миграции Alembic
│   ├── versions/            # Файлы миграций
│   ├── env.py               # Конфигурация Alembic
│   └── script.py.mako       # Шаблон миграций
├── alembic.ini              # Конфигурация Alembic
├── requirements.txt         # Зависимости проекта
├── requirements-dev.txt    # Зависимости для разработки
├── init_db.py              # CLI для управления БД
├── check_setup.py          # Проверка установки
├── Makefile                # Команды управления
└── .pre-commit-config.yaml # Pre-commit хуки
```

## База данных

### Структура таблиц

#### users
- `id` UUID - первичный ключ
- `email` VARCHAR(255) UNIQUE - email пользователя
- `auth_hash` VARCHAR(255) - хэш мастер-пароля
- `crypto_salt` VARCHAR(255) - соль для криптографических операций
- `encrypted_vault_key` TEXT - зашифрованный ключ хранилища
- `created_at`, `updated_at` TIMESTAMPTZ - временные метки

#### sessions
- `id` UUID - первичный ключ (Bearer-токен)
- `user_id` UUID - внешний ключ к users (каскадное удаление)
- `device_info` VARCHAR(255) - информация об устройстве
- `is_revoked` BOOLEAN - флаг отзыва сессии
- `expires_at` TIMESTAMPTZ - время истечения сессии (TTL 12 часов)
- `created_at` TIMESTAMPTZ - временная метка создания

#### vault_items
- `id` UUID - первичный ключ
- `user_id` UUID - внешний ключ к users (каскадное удаление)
- `encrypted_title` TEXT - зашифрованное название сервиса
- `title_blind_index` VARCHAR(255) - слепой индекс для поиска
- `encrypted_login` TEXT - зашифрованный логин
- `encrypted_password` TEXT - зашифрованный пароль
- `encrypted_url` TEXT - зашифрованный URL
- `encrypted_comment` TEXT - зашифрованный комментарий
- `created_at`, `updated_at` TIMESTAMPTZ - временные метки

### Управление базой данных

```bash
# Инициализация базы данных
make db-init

# Сброс базы данных
make db-reset

# Загрузка тестовых данных
make db-test

# Проверка подключения
make db-check

# Применение миграций Alembic
make migrate

# Создание новой миграции
make migrate-create

# Откат последней миграции
make migrate-rollback
```

## API эндпоинты

### Аутентификация
- `POST /api/auth/register` - Регистрация пользователя
- `GET /api/auth/params` - Получение криптографических параметров
- `POST /api/auth/login` - Вход в систему
- `POST /api/auth/logout` - Выход из системы

### Пользователь
- `PUT /api/users/me/password` - Смена мастер-пароля
- `DELETE /api/users/me` - Удаление аккаунта

### Хранилище
- `GET /api/vault/items` - Получение списка паролей
- `POST /api/vault/items` - Добавление нового пароля
- `GET /api/vault/items/{id}` - Получение конкретного пароля
- `PUT /api/vault/items/{id}` - Обновление пароля
- `DELETE /api/vault/items/{id}` - Удаление пароля

## Разработка

### Тестирование

```bash
# Запуск всех тестов
make test

# Запуск тестов моделей
make test-models

# Запуск тестов схем
make test-schemas

# Покрытие кода тестами
pytest --cov=app --cov-report=html
```

### Линтинг и форматирование

```bash
# Проверка кода линтерами
make lint

# Форматирование кода
make format

# Установка pre-commit хуков
pre-commit install
```

### Команды Makefile

```bash
# Показать все команды
make help

# Полная установка проекта
make setup

# Запуск CI pipeline
make ci

# Очистка кэша и временных файлов
make clean
```

## Безопасность

### Zero-Knowledge принципы
1. Мастер-пароль никогда не передается на сервер
2. Все шифрование выполняется на стороне клиента
3. Сервер хранит только хэши и зашифрованные данные
4. Ключ хранилища шифруется мастер-паролем на клиенте

### Rate Limiting
- `5/минуту` для эндпоинтов аутентификации
- `30/минуту` для операций записи
- `120/минуту` для остальных эндпоинтов

### Защита данных
- Слепые индексы для поиска по зашифрованным данным
- Каскадное удаление связанных данных
- TTL сессий (12 часов)
- Отзыв всех сессий при смене пароля

## Развертывание

### Production настройки

1. **Отключите debug режим**: `DEBUG=false`
2. **Отключите документацию**: `DOCS_ENABLED=false`
3. **Настройте CORS origins**: Укажите домены фронтенда
4. **Используйте Redis для rate limiting**: `RATE_LIMIT_STORAGE_URI=redis://...`
5. **Используйте безопасный секретный ключ**
6. **Настройте HTTPS и SSL/TLS**

### Мониторинг и логирование

1. **Логирование запросов**: Настройте structured logging
2. **Метрики**: Добавьте Prometheus метрики
3. **Health checks**: Реализуйте `/health` эндпоинт
4. **Алертинг**: Настройте мониторинг ошибок

## Лицензия

[Укажите лицензию проекта]