# -*- coding: utf-8 -*-
"""
Модуль конфигурации бота
"""

import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class Config:
    """Класс для управления конфигурацией бота"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Инициализация конфигурации
        
        Args:
            config_path: Путь к файлу конфигурации (опционально)
        """
        # Загружаем переменные окружения из .env файла
        load_dotenv()
        
        # Базовые пути
        self.base_dir = Path(__file__).parent.parent
        self.config_path = config_path or self.base_dir / "config.json"
        
        # Загружаем конфигурацию
        self._load_config()
        
    def _load_config(self):
        """Загрузка конфигурации из файла и переменных окружения"""
        # Значения по умолчанию
        defaults = {
            "token": "",
            "prefix": "!",
            "sync_commands_on_start": True,
            "database_path": "data/bot.db",
            "logs_dir": "logs",
            "log_level": "INFO",
            "log_retention_days": 30,
            "max_log_size_mb": 10,
            "global_admins": [],
            "default_language": "ru",
            "number_formats": [
                "^\\d+\\.\\s*",
                "^\\d+\\s*\\|\\|\\s*",
                "^\\d+\\s*",
                "^\\d+\\s*-\\s*",
                "^\\[\\d+\\]\\s*"
            ],
            "features": {
                "auto_save_hosts": True,
                "multi_language": False,
                "slash_commands": True,
                "web_dashboard": False
            }
        }
        
        # Загружаем из файла, если существует
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    defaults.update(file_config)
                    logger.info(f"Конфигурация загружена из {self.config_path}")
            except Exception as e:
                logger.error(f"Ошибка загрузки конфигурации: {e}")
        
        # Переопределяем значения из переменных окружения
        self.token = os.getenv('DISCORD_TOKEN', defaults.get('token', ''))
        self.prefix = os.getenv('BOT_PREFIX', defaults.get('prefix', '!'))
        self.sync_commands_on_start = os.getenv(
            'SYNC_COMMANDS_ON_START', 
            str(defaults.get('sync_commands_on_start', True))
        ).lower() == 'true'
        
        # Пути
        self.database_path = Path(os.getenv(
            'DATABASE_PATH', 
            defaults.get('database_path', 'data/bot.db')
        ))
        if not self.database_path.is_absolute():
            self.database_path = self.base_dir / self.database_path
            
        self.logs_dir = Path(os.getenv(
            'LOGS_DIR', 
            defaults.get('logs_dir', 'logs')
        ))
        if not self.logs_dir.is_absolute():
            self.logs_dir = self.base_dir / self.logs_dir
            
        # Логирование
        self.log_level = os.getenv('LOG_LEVEL', defaults.get('log_level', 'INFO'))
        self.log_retention_days = int(os.getenv(
            'LOG_RETENTION_DAYS', 
            defaults.get('log_retention_days', 30)
        ))
        self.max_log_size_mb = int(os.getenv(
            'MAX_LOG_SIZE_MB', 
            defaults.get('max_log_size_mb', 10)
        ))
        
        # Администраторы
        global_admins_env = os.getenv('GLOBAL_ADMINS', '')
        if global_admins_env:
            self.global_admins = [int(x.strip()) for x in global_admins_env.split(',') if x.strip()]
        else:
            self.global_admins = defaults.get('global_admins', [])
            
        # Прочие настройки
        self.default_language = os.getenv('DEFAULT_LANGUAGE', defaults.get('default_language', 'ru'))
        self.number_formats = defaults.get('number_formats', [])
        self.features = defaults.get('features', {})
        
        # Создаём необходимые директории
        self._create_directories()
        
    def _create_directories(self):
        """Создание необходимых директорий"""
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        
    def save(self):
        """Сохранение текущей конфигурации в файл"""
        config_data = {
            "prefix": self.prefix,
            "sync_commands_on_start": self.sync_commands_on_start,
            "database_path": str(self.database_path.relative_to(self.base_dir)),
            "logs_dir": str(self.logs_dir.relative_to(self.base_dir)),
            "log_level": self.log_level,
            "log_retention_days": self.log_retention_days,
            "max_log_size_mb": self.max_log_size_mb,
            "global_admins": self.global_admins,
            "default_language": self.default_language,
            "number_formats": self.number_formats,
            "features": self.features
        }
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            logger.info("Конфигурация сохранена")
        except Exception as e:
            logger.error(f"Ошибка сохранения конфигурации: {e}")
            
    def get_example_env(self) -> str:
        """Получить пример .env файла"""
        return """# Discord Bot Token (обязательно!)
DISCORD_TOKEN=your_bot_token_here

# Префикс команд
BOT_PREFIX=!

# Синхронизировать команды при запуске
SYNC_COMMANDS_ON_START=true

# Путь к базе данных
DATABASE_PATH=data/bot.db

# Директория для логов
LOGS_DIR=logs

# Уровень логирования (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Сколько дней хранить логи
LOG_RETENTION_DAYS=30

# Максимальный размер лог-файла в МБ
MAX_LOG_SIZE_MB=10

# Глобальные администраторы (ID через запятую)
GLOBAL_ADMINS=123456789,987654321

# Язык по умолчанию
DEFAULT_LANGUAGE=ru
""" 