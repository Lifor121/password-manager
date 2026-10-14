# Makefile для управления проектом менеджера паролей

.PHONY: help install dev test lint format db-init db-reset db-test migrate

# Цвета для вывода
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Показать помощь
	@echo "Использование: make <цель>"
	@echo ""
	@echo "Цели:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Установить зависимости
	@echo "$(YELLOW)Установка зависимостей...$(NC)"
	pip install -r requirements.txt -r requirements-dev.txt

dev: ## Запустить сервер для разработки
	@echo "$(YELLOW)Запуск сервера для разработки...$(NC)"
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test: ## Запустить тесты
	@echo "$(YELLOW)Запуск тестов...$(NC)"
	pytest -v --cov=app --cov-report=term-missing

test-models: ## Запустить тесты моделей
	@echo "$(YELLOW)Запуск тестов моделей...$(NC)"
	pytest tests/test_models.py -v

test-schemas: ## Запустить тесты схем
	@echo "$(YELLOW)Запуск тестов схем...$(NC)"
	pytest tests/test_schemas.py -v

lint: ## Проверить код линтерами
	@echo "$(YELLOW)Проверка кода линтерами...$(NC)"
	ruff check .
	mypy app

format: ## Форматировать код
	@echo "$(YELLOW)Форматирование кода...$(NC)"
	black app tests
	ruff check . --fix

db-init: ## Инициализировать базу данных
	@echo "$(YELLOW)Инициализация базы данных...$(NC)"
	python init_db.py init

db-reset: ## Сбросить базу данных
	@echo "$(YELLOW)Сброс базы данных...$(NC)"
	python init_db.py reset

db-test: ## Загрузить тестовые данные
	@echo "$(YELLOW)Загрузка тестовых данных...$(NC)"
	python init_db.py load-test-data

db-check: ## Проверить подключение к базе данных
	@echo "$(YELLOW)Проверка подключения к базе данных...$(NC)"
	python init_db.py check

migrate: ## Применить миграции
	@echo "$(YELLOW)Применение миграций...$(NC)"
	alembic upgrade head

migrate-create: ## Создать новую миграцию
	@echo "$(YELLOW)Создание новой миграции...$(NC)"
	@read -p "Введите описание миграции: " desc; \
	alembic revision --autogenerate -m "$$desc"

migrate-rollback: ## Откатить последнюю миграцию
	@echo "$(YELLOW)Откат последней миграции...$(NC)"
	alembic downgrade -1

clean: ## Очистить кэш и временные файлы
	@echo "$(YELLOW)Очистка кэша и временных файлов...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true

setup: install db-init db-test ## Полная установка проекта

ci: lint test ## Запуск CI pipeline (линтеры + тесты)

.DEFAULT_GOAL := help