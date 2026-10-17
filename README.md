# Password Manager

Zero-knowledge менеджер паролей: **SvelteKit** (frontend) + **FastAPI** (backend) + **PostgreSQL**.

## Быстрый старт (Docker)

```bash
cp .env.example .env
# задайте POSTGRES_PASSWORD в .env
docker compose up -d --build
```

Приложение: **http://localhost:8080**

Полная инструкция по развёртыванию, настройке и эксплуатации: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## Структура

- [frontend/](frontend/) — SvelteKit SPA (шифрование на клиенте)
- [backend/](backend/) — FastAPI, Alembic, PostgreSQL ([backend/README.md](backend/README.md))
- [docs/](docs/) — документация API и БД
- `docker-compose.yml` — единый запуск всего стека
