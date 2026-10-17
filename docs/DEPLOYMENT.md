# Развёртывание через Docker

Самый простой способ запустить весь проект (frontend + backend + PostgreSQL) — **одна команда**. Не нужно ставить Python, Node.js или PostgreSQL на сервер.

## Что понадобится

- [Docker](https://docs.docker.com/get-docker/) версии 20.10+ (в комплекте с Docker Compose v2)
- Не более 2 ГБ свободного места на диске (образы + данные БД)

## Быстрый старт

```bash
# 1. Скопировать шаблон окружения
cp .env.example .env

# 2. Открыть .env и задать пароль базы данных (обязательно!)
#    POSTGRES_PASSWORD=очень-надёжный-пароль

# 3. Запустить всё
docker compose up -d --build
```

Готово. Через пару минут приложение доступно на **http://localhost:8080**

- Приложение: `http://localhost:8080`
- Health backend'а: `http://localhost:8080/health` (через nginx-прокси)

API-документация (если включена, см. `DOCS_ENABLED`): `http://localhost:8080/docs`

## Как это устроено

```
docker compose
├── db        postgres:16-alpine          — база данных (volume pgdata)
├── backend   ./backend (FastAPI)         — ждёт БД, применяет миграции Alembic, запускает uvicorn
└── frontend  ./frontend (SvelteKit+nginx) — раздаёт статику и проксирует /api на backend
```

Ключевые моменты:

- **Backend сам ждёт базу** — при старте entrypoint подключается к PostgreSQL (до 60 секунд), затем применяет миграции `alembic upgrade head` и только потом запускает API. Поэтому `docker compose up` работает «с нуля» без ручных шагов.
- **Frontend и API на одном origin** — nginx проксирует `/api/*` и `/health` на backend, поэтому не нужно настраивать CORS для обычного развёртывания.
- **Порт backend наружу не публикуется** — весь трафик идёт через nginx.
- Данные базы хранятся в named volume `pgdata` и переживают пересоздание контейнеров.

## Переменные окружения (.env)

Файл `.env` рядом с `docker-compose.yml` (см. `.env.example`):

| Переменная | По умолчанию | Описание |
|---|---|---|
| `POSTGRES_USER` | `postgres` | Пользователь БД |
| `POSTGRES_PASSWORD` | — (**обязательна**) | Пароль БД |
| `POSTGRES_DB` | `password_manager` | Имя базы данных |
| `FRONTEND_PORT` | `8080` | Порт приложения на хосте |
| `ENVIRONMENT` | `production` | Режим приложения |
| `DEBUG` | `false` | Debug-режим API |
| `DOCS_ENABLED` | `false` | Включить `/docs` (Swagger). Для продакшена держите `false` |
| `CORS_ORIGINS` | `http://localhost:8080` | Origin'ы фронтенда через запятую (обычно не требуется: `/api` идёт через nginx) |
| `RATE_LIMIT_STORAGE_URI` | пусто | Пусто = счётчики в памяти (ок для одного воркера). Для кластера: `redis://redis:6379/0` |

После изменения `.env` примените новые значения:

```bash
docker compose up -d
```

(Если менялись build-параметры — `docker compose up -d --build`.)

## Типовые операции

```bash
# Статус контейнеров
docker compose ps

# Логи (все / конкретного сервиса)
docker compose logs -f
docker compose logs -f backend

# Остановить (данные БД сохраняются в volume)
docker compose down

# Остановить и УДАЛИТЬ данные БД (необратимо!)
docker compose down -v

# Пересобрать backend после изменения кода
docker compose up -d --build backend

# Применить миграции вручную (обычно не нужно — они применяются при старте)
docker compose exec backend alembic upgrade head

# Проверить подключение к БД
docker compose exec backend python init_db.py check
```

## Продакшен-рекомендации

1. **Пароли.** Задайте реальный `POSTGRES_PASSWORD` в `.env`; файл `.env` не коммитится (в `.gitignore`).
2. **HTTPS.** nginx в образе слушает только HTTP. Поставьте перед приложением Reverse-proxy с TLS — готовое решение: [Traefik](https://traefik.io/) или [Caddy](https://caddyserver.com/), либо корпоративный nginx/certbot. Простейший вариант с nginx+certbot описан [здесь](https://certbot.eff.org/instructions?ws=nginx&os=debian).
3. **Бэкапы БД.**

   ```bash
   # Бэкап
   docker compose exec db pg_dump -U postgres password_manager > backup_$(date +%F).sql

   # Восстановление
   docker compose exec -T db psql -U postgres password_manager < backup_$(date +%F).sql
   ```

4. **Обновление версии.** `git pull && docker compose up -d --build` — миграции применятся автоматически.
5. **Ресурсы.** Ограничить контейнеры можно через `deploy.resources.limits` в `docker-compose.yml`.

## Частые проблемы

| Симптом | Решение |
|---|---|
| `Задайте POSTGRES_PASSWORD в .env` при запуске | Создайте `.env` из `.env.example` и задайте пароль |
| Backend перезапускается с ошибкой «Database did not become ready» | База не поднялась: `docker compose logs db`. Проверьте, не занят ли порт и не остался ли «сломанный» volume от старых настроек (`docker compose down -v` — удалит данные!) |
| Порт 8080 уже занят | Задайте другой `FRONTEND_PORT` в `.env` |
| Изменил код фронта, но изменений нет в браузере | `docker compose up -d --build frontend`; затем жёсткая перезагрузка страницы (Ctrl+Shift+R) |
| 429 от API при активной разработке | Это rate limiting (5/мин на auth). Лимиты настраиваются в `.env` (`RATE_LIMIT_AUTH` и др.) |

## Развёртывание на удалённом сервере

```bash
# на сервере
git clone <repository-url> password-manager && cd password-manager
cp .env.example .env && nano .env        # задать POSTGRES_PASSWORD
docker compose up -d --build
```

Приложение будет доступно на `http://<ip-сервера>:8080`. Не забудьте открыть порт в файрволе и настроить HTTPS (см. «Продакшен-рекомендации»).
