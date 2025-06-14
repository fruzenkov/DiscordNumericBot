# -*- coding: utf-8 -*-
"""
Модуль для работы с базой данных
"""

import aiosqlite
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Database:
    """Класс для работы с базой данных SQLite"""
    
    def __init__(self, db_path: Path):
        """
        Инициализация базы данных
        
        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = db_path
        self.connection: Optional[aiosqlite.Connection] = None
        
    async def initialize(self):
        """Инициализация базы данных и создание таблиц"""
        try:
            self.connection = await aiosqlite.connect(str(self.db_path))
            await self._create_tables()
            logger.info(f"База данных инициализирована: {self.db_path}")
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
            raise
            
    async def _create_tables(self):
        """Создание необходимых таблиц"""
        async with self.connection.executescript("""
            -- Таблица серверов
            CREATE TABLE IF NOT EXISTS guilds (
                guild_id INTEGER PRIMARY KEY,
                guild_name TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                settings TEXT DEFAULT '{}'
            );
            
            -- Таблица пользователей с правами
            CREATE TABLE IF NOT EXISTS authorized_users (
                user_id INTEGER,
                guild_id INTEGER,
                role TEXT,  -- 'admin', 'moderator', 'host'
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, guild_id),
                FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)
            );
            
            -- Таблица ведущих (хостов)
            CREATE TABLE IF NOT EXISTS hosts (
                host_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                nickname TEXT,
                is_active BOOLEAN DEFAULT 1,
                sessions_count INTEGER DEFAULT 0,
                last_session TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)
            );
            
            -- Таблица сессий нумерации
            CREATE TABLE IF NOT EXISTS numbering_sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                channel_id INTEGER,
                host_id INTEGER,
                participants_count INTEGER,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                FOREIGN KEY (guild_id) REFERENCES guilds(guild_id),
                FOREIGN KEY (host_id) REFERENCES hosts(host_id)
            );
            
            -- Таблица логов действий
            CREATE TABLE IF NOT EXISTS action_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                action TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)
            );
            
            -- Индексы для производительности
            CREATE INDEX IF NOT EXISTS idx_hosts_guild ON hosts(guild_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_guild ON numbering_sessions(guild_id);
            CREATE INDEX IF NOT EXISTS idx_logs_guild ON action_logs(guild_id);
            CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON action_logs(timestamp);
        """):
            pass
            
    async def ensure_guild_exists(self, guild_id: int, guild_name: str = None) -> None:
        """Убедиться, что сервер существует в базе данных"""
        async with self.connection.execute(
            "INSERT OR IGNORE INTO guilds (guild_id, guild_name) VALUES (?, ?)",
            (guild_id, guild_name)
        ):
            await self.connection.commit()
            
    async def get_guild_settings(self, guild_id: int) -> Dict[str, Any]:
        """Получить настройки сервера"""
        async with self.connection.execute(
            "SELECT settings FROM guilds WHERE guild_id = ?",
            (guild_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return json.loads(row[0])
            return {}
            
    async def update_guild_settings(self, guild_id: int, settings: Dict[str, Any]) -> None:
        """Обновить настройки сервера"""
        await self.ensure_guild_exists(guild_id)
        async with self.connection.execute(
            "UPDATE guilds SET settings = ? WHERE guild_id = ?",
            (json.dumps(settings, ensure_ascii=False), guild_id)
        ):
            await self.connection.commit()
            
    async def add_authorized_user(self, guild_id: int, user_id: int, role: str, added_by: int) -> None:
        """Добавить авторизованного пользователя"""
        async with self.connection.execute(
            """INSERT OR REPLACE INTO authorized_users 
               (user_id, guild_id, role, added_by) 
               VALUES (?, ?, ?, ?)""",
            (user_id, guild_id, role, added_by)
        ):
            await self.connection.commit()
            
    async def remove_authorized_user(self, guild_id: int, user_id: int) -> None:
        """Удалить авторизованного пользователя"""
        async with self.connection.execute(
            "DELETE FROM authorized_users WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        ):
            await self.connection.commit()
            
    async def get_authorized_users(self, guild_id: int) -> List[Dict[str, Any]]:
        """Получить список авторизованных пользователей"""
        async with self.connection.execute(
            """SELECT user_id, role, added_by, added_at 
               FROM authorized_users 
               WHERE guild_id = ?""",
            (guild_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "user_id": row[0],
                    "role": row[1],
                    "added_by": row[2],
                    "added_at": row[3]
                }
                for row in rows
            ]
            
    async def add_or_update_host(self, guild_id: int, user_id: int, nickname: str) -> int:
        """Добавить или обновить ведущего"""
        # Проверяем, существует ли уже такой ведущий
        async with self.connection.execute(
            "SELECT host_id FROM hosts WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        ) as cursor:
            row = await cursor.fetchone()
            
        if row:
            # Обновляем существующего
            host_id = row[0]
            async with self.connection.execute(
                """UPDATE hosts 
                   SET nickname = ?, is_active = 1 
                   WHERE host_id = ?""",
                (nickname, host_id)
            ):
                await self.connection.commit()
        else:
            # Создаём нового
            async with self.connection.execute(
                """INSERT INTO hosts (guild_id, user_id, nickname) 
                   VALUES (?, ?, ?)""",
                (guild_id, user_id, nickname)
            ) as cursor:
                host_id = cursor.lastrowid
                await self.connection.commit()
                
        return host_id
        
    async def get_active_hosts(self, guild_id: int) -> List[Dict[str, Any]]:
        """Получить список активных ведущих"""
        async with self.connection.execute(
            """SELECT host_id, user_id, nickname, sessions_count, last_session 
               FROM hosts 
               WHERE guild_id = ? AND is_active = 1 
               ORDER BY sessions_count DESC""",
            (guild_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "host_id": row[0],
                    "user_id": row[1],
                    "nickname": row[2],
                    "sessions_count": row[3],
                    "last_session": row[4]
                }
                for row in rows
            ]
            
    async def start_numbering_session(self, guild_id: int, channel_id: int, 
                                    host_id: int, participants_count: int) -> int:
        """Начать сессию нумерации"""
        async with self.connection.execute(
            """INSERT INTO numbering_sessions 
               (guild_id, channel_id, host_id, participants_count) 
               VALUES (?, ?, ?, ?)""",
            (guild_id, channel_id, host_id, participants_count)
        ) as cursor:
            session_id = cursor.lastrowid
            
        # Обновляем статистику ведущего
        async with self.connection.execute(
            """UPDATE hosts 
               SET sessions_count = sessions_count + 1, 
                   last_session = CURRENT_TIMESTAMP 
               WHERE host_id = ?""",
            (host_id,)
        ):
            await self.connection.commit()
            
        return session_id
        
    async def end_numbering_session(self, session_id: int) -> None:
        """Завершить сессию нумерации"""
        async with self.connection.execute(
            "UPDATE numbering_sessions SET ended_at = CURRENT_TIMESTAMP WHERE session_id = ?",
            (session_id,)
        ):
            await self.connection.commit()
            
    async def log_action(self, guild_id: int, user_id: int, action: str, details: str = "") -> None:
        """Записать действие в лог"""
        async with self.connection.execute(
            """INSERT INTO action_logs (guild_id, user_id, action, details) 
               VALUES (?, ?, ?, ?)""",
            (guild_id, user_id, action, details)
        ):
            await self.connection.commit()
            
    async def get_recent_logs(self, guild_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Получить последние логи"""
        async with self.connection.execute(
            """SELECT log_id, user_id, action, details, timestamp 
               FROM action_logs 
               WHERE guild_id = ? 
               ORDER BY timestamp DESC 
               LIMIT ?""",
            (guild_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "log_id": row[0],
                    "user_id": row[1],
                    "action": row[2],
                    "details": row[3],
                    "timestamp": row[4]
                }
                for row in rows
            ]
            
    async def get_statistics(self, guild_id: int) -> Dict[str, Any]:
        """Получить статистику сервера"""
        stats = {}
        
        # Количество сессий
        async with self.connection.execute(
            "SELECT COUNT(*) FROM numbering_sessions WHERE guild_id = ?",
            (guild_id,)
        ) as cursor:
            stats['total_sessions'] = (await cursor.fetchone())[0]
            
        # Количество ведущих
        async with self.connection.execute(
            "SELECT COUNT(*) FROM hosts WHERE guild_id = ? AND is_active = 1",
            (guild_id,)
        ) as cursor:
            stats['active_hosts'] = (await cursor.fetchone())[0]
            
        # Топ ведущих
        async with self.connection.execute(
            """SELECT user_id, nickname, sessions_count 
               FROM hosts 
               WHERE guild_id = ? AND is_active = 1 
               ORDER BY sessions_count DESC 
               LIMIT 5""",
            (guild_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            stats['top_hosts'] = [
                {
                    "user_id": row[0],
                    "nickname": row[1],
                    "sessions_count": row[2]
                }
                for row in rows
            ]
            
        return stats
        
    async def close(self):
        """Закрыть соединение с базой данных"""
        if self.connection:
            await self.connection.close()
            logger.info("Соединение с базой данных закрыто") 