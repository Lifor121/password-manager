#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных.
Использование: python init_db.py [команда]

Команды:
  init    - создать таблицы
  drop    - удалить все таблицы
  reset   - удалить и заново создать таблицы
  test    - загрузить тестовые данные
"""

import sys
import asyncio
from typing import List

import click
from sqlalchemy import text

from app.core.database import init_db, drop_db, AsyncSessionLocal


@click.group()
def cli():
    """CLI для управления базой данных"""
    pass


@cli.command()
def init():
    """Создать таблицы в базе данных"""
    print("Создание таблиц...")
    init_db()
    print("✅ Таблицы созданы успешно")


@cli.command()
def drop():
    """Удалить все таблицы из базы данных"""
    confirm = input("Вы уверены, что хотите удалить все таблицы? (yes/no): ")
    if confirm.lower() == "yes":
        print("Удаление таблиц...")
        drop_db()
        print("✅ Таблицы удалены успешно")
    else:
        print("❌ Операция отменена")


@cli.command()
def reset():
    """Удалить и заново создать таблицы"""
    print("Сброс базы данных...")
    drop_db()
    init_db()
    print("✅ База данных сброшена успешно")


@cli.command()
@click.option("--file", default="database/test_data.sql", help="Путь к SQL файлу с тестовыми данными")
def load_test_data(file: str):
    """Загрузить тестовые данные из SQL файла"""
    try:
        with open(file, "r", encoding="utf-8") as f:
            sql_content = f.read()
        
        # Разделяем SQL на отдельные команды
        commands = [cmd.strip() for cmd in sql_content.split(";") if cmd.strip()]
        
        print(f"Загрузка тестовых данных из {file}...")
        
        async def execute_commands():
            async with AsyncSessionLocal() as session:
                for command in commands:
                    if command:  # Пропускаем пустые команды
                        try:
                            await session.execute(text(command))
                        except Exception as e:
                            print(f"⚠️  Ошибка при выполнении команды: {command[:50]}...")
                            print(f"   Ошибка: {e}")
                            await session.rollback()
                            return
                await session.commit()
        
        asyncio.run(execute_commands())
        print("✅ Тестовые данные загружены успешно")
        
    except FileNotFoundError:
        print(f"❌ Файл {file} не найден")
    except Exception as e:
        print(f"❌ Ошибка при загрузке тестовых данных: {e}")


@cli.command()
def check():
    """Проверить подключение к базе данных"""
    async def check_connection():
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT version()"))
                version = result.scalar()
                print(f"✅ Подключение к PostgreSQL успешно")
                print(f"   Версия: {version}")
                
                # Проверка существования таблиц
                tables_result = await session.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
                tables = [row[0] for row in tables_result.fetchall()]
                
                if tables:
                    print(f"✅ Найдено таблиц: {len(tables)}")
                    for table in tables:
                        print(f"   - {table}")
                else:
                    print("ℹ️  Таблицы не найдены. Используйте команду 'init' для создания таблиц")
                    
        except Exception as e:
            print(f"❌ Ошибка подключения к базе данных: {e}")
            print("   Проверьте настройки подключения в .env файле")
    
    asyncio.run(check_connection())


@cli.command()
def tables_sql():
    """Показать SQL для создания таблиц"""
    from app.models.base import Base
    from app.models.user import User
    from app.models.session import Session
    from app.models.vault_item import VaultItem
    
    print("-- SQL для создания таблиц базы данных менеджера паролей")
    print("-- Сгенерировано автоматически из SQLAlchemy моделей")
    print()
    
    for table in Base.metadata.sorted_tables:
        print(f"-- Таблица: {table.name}")
        print(str(table.compile(engine)))
        print()
    
    print("-- Индексы:")
    for table in Base.metadata.sorted_tables:
        for index in table.indexes:
            print(f"-- {index.name}: {str(index.compile(engine))}")


if __name__ == "__main__":
    cli()