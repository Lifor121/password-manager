# CI/CD и автоматический деплой (GitHub Actions)

В проекте настроен полный пайплайн непрерывной интеграции и развёртывания (CI/CD) на базе **GitHub Actions** (`.github/workflows/ci-cd.yml`).

---

## Архитектура пайплайна

Пайплайн построен по лучшим индустриальным практикам GitFlow / GitHub Flow:

| Ветка / Событие | Что выполняется | Деплой |
|---|---|:---:|
| **Push в `develop`** | Проверка качества кода: линтинг, типизация, тесты бэкенда и фронтенда, валидация Docker Compose | ❌ Нет |
| **Pull Request (в `develop` или `main`)** | Полный набор проверок качества (CI) | ❌ Нет |
| **Push в `main`** | Сначала запускаются все CI-проверки. Если они успешны — автоматически запускается деплой на сервер | ✅ **Да** |
| **Workflow Dispatch** (ручной запуск) | Ручной запуск из вкладки Actions в GitHub (с опцией принудительного деплоя) | Опционально |

### Состав проверок (CI)

1. **Backend CI (`backend-ci`)**:
   - Python 3.12 (кэширование pip).
   - Линтинг кода: `ruff check .`
   - Статическая проверка типов: `mypy app`
   - Автотесты с проверкой покрытия: `pytest -v --cov=app`
2. **Frontend CI (`frontend-ci`)**:
   - Node.js 22 (кэширование npm через `package-lock.json`).
   - Проверка форматирования и линтинга: `npm run lint` (Prettier + ESLint).
   - Проверка типов SvelteKit / TypeScript: `npm run check` (`svelte-check`).
   - Запуск тестов: `npm run test` (Vitest + Playwright headless Chromium).
   - Сборка продакшен-бандла: `npm run build`.
3. **Docker Compose Validation (`docker-ci`)**:
   - Валидация синтаксиса и интерполяции переменных `docker compose config --quiet`.

---

## Настройка Nginx Proxy Manager (NPM)

В `docker-compose.yml` наружу опубликован только сервис **frontend**:
```yaml
ports:
  - "${FRONTEND_PORT:-8080}:80"
```
Frontend-контейнер (Nginx) внутри слушает порт `80` и сам проксирует запросы `/api/*` на бэкенд (`backend:8000`).

Поэтому в **Nginx Proxy Manager** (когда он и фронтенд находятся в сети `proxy-net`) Proxy Host настраивается напрямую по имени контейнера и порту 80:

### Параметры Proxy Host в NPM (сеть `proxy-net`):

| Поле в NPM | Значение | Пояснение |
|---|---|---|
| **Domain Names** | `passwords.example.com` (ваш домен) | Домен, по которому будет открываться менеджер |
| **Scheme** | `http` | Внутреннее соединение между NPM и приложением |
| **Forward Hostname / IP** | `password-manager-frontend` | Имя алиаса сервиса в сети `proxy-net` (также доступно `frontend`) |
| **Forward Port** | **`80`** | **Внутренний порт контейнера frontend** |
| **Cache Assets** | `Включено` (по желанию) | Кэширование статики |
| **Block Common Exploits** | `Включено` | Защита от типовых атак |
| **Websockets Support** | `Включено` | Рекомендуется для SPA и сокетов |

> [!NOTE]
> В `docker-compose.yml` настроена универсальная интеграция:
> - **На сервере:** в `.env` задано `EXTERNAL_PROXY_NET=true`, контейнер подключается к существующей сети `proxy-net`, а NPM проксирует на `password-manager-frontend:80`.
> - **Локально:** `EXTERNAL_PROXY_NET=false` (по умолчанию), Compose автоматически создаёт локальную сеть и приложение доступно на `http://localhost:8080`.

### Вкладка SSL в NPM:
- **SSL Certificate**: Request a new SSL Certificate (Let's Encrypt).
- **Force SSL**: Включено.
- **HTTP/2 Support**: Включено.
- **HSTS Enabled**: Включено.

---

## Секреты для GitHub Actions (GitHub Secrets)

Для работы деплоя перейдите в ваш репозиторий на GitHub:
**Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**.

### 1. Настройки SSH подключения к серверу:

| Секрет | Обязательный? | Описание | Пример |
|---|:---:|---|---|
| `SSH_HOST` | **Да** | IP-адрес или домен вашего VPS/сервера | `194.87.x.x` или `srv.example.com` |
| `SSH_USER` | **Да** | Пользователь SSH с доступом к Docker | `root` или `ubuntu` |
| `SSH_KEY` | **Да** | Приватный SSH-ключ (OpenSSH / ed25519 / rsa) | Содержимое `~/.ssh/id_ed25519` |
| `SSH_PORT` | Нет | Порт SSH (если нестандартный) | `22` (по умолчанию 22) |
| `DEPLOY_PATH` | **Да** | Абсолютный путь к проекту на сервере | `/opt/password-manager` |

### 2. Переменные приложения:

| Секрет | Обязательный? | Описание | Значение по умолчанию |
|---|:---:|---|---|
| `POSTGRES_PASSWORD` | **Да** | Надёжный пароль для базы данных PostgreSQL | — |
| `POSTGRES_USER` | Нет | Имя пользователя базы данных | `postgres` |
| `POSTGRES_DB` | Нет | Имя базы данных | `password_manager` |
| `FRONTEND_PORT` | Нет | Внешний порт приложения на хосте | `8080` |
| `CORS_ORIGINS` | Нет | Разрешённые CORS-источники | `http://localhost:8080` |
| `ENVIRONMENT` | Нет | Режим окружения | `production` |
| `ENV_CONTENT` | Нет | (Альтернатива) Полный текст `.env` файла целиком | Если задан, имеет приоритет |

---

## Первоначальная подготовка сервера (однократно)

Перед первым автоматическим деплоем выполните на сервере:

```bash
# 1. Установите Docker и Docker Compose (если ещё не установлены)
curl -fsSL https://get.docker.com | sh

# 2. Склонируйте репозиторий в целевую директорию
sudo mkdir -p /opt/password-manager
sudo chown -R $USER:$USER /opt/password-manager
git clone <URL_ВАШЕГО_РЕПОЗИТОРИЯ> /opt/password-manager

# 3. Добавьте публичный SSH-ключ в authorized_keys
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
```

После пуша в `main` GitHub Actions подключится к серверу, актуализирует код, сформирует `.env` из секретов, соберёт образы и перезапустит контейнеры без простоя:
```bash
docker compose pull --ignore-buildable || true
docker compose up -d --build --remove-orphans
docker image prune -f
```
Alembic-миграции базы данных применяются автоматически при старте бэкенда.
