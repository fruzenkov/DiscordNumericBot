# -*- coding: utf-8 -*-
"""
Модуль настройки логирования
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Цветные логи для консоли
try:
    import colorlog
    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False


def setup_logger(name: str = None, 
                log_dir: Path = None, 
                log_level: str = "INFO",
                max_bytes: int = 10 * 1024 * 1024,  # 10MB
                backup_count: int = 30) -> logging.Logger:
    """
    Настройка логгера с ротацией файлов и цветным выводом
    
    Args:
        name: Имя логгера
        log_dir: Директория для логов
        log_level: Уровень логирования
        max_bytes: Максимальный размер файла лога
        backup_count: Количество резервных копий
        
    Returns:
        Настроенный логгер
    """
    # Получаем или создаём логгер
    logger = logging.getLogger(name)
    
    # Избегаем дублирования обработчиков
    if logger.handlers:
        return logger
        
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Форматирование
    file_format = '%(asctime)s | %(name)-20s | %(levelname)-8s | %(funcName)-20s | %(message)s'
    console_format = '%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Обработчик для файла
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Имя файла с текущей датой
        log_file = log_dir / f"bot_{datetime.now().strftime('%Y-%m-%d')}.log"
        
        # Ротация по размеру
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(file_format, datefmt=date_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Обработчик для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    if COLORLOG_AVAILABLE:
        # Цветной вывод
        console_formatter = colorlog.ColoredFormatter(
            f'%(log_color)s{console_format}',
            datefmt=date_format,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
    else:
        console_formatter = logging.Formatter(console_format, datefmt=date_format)
        
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Отключаем пропаганду логов вверх по иерархии
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Получить существующий логгер
    
    Args:
        name: Имя логгера
        
    Returns:
        Логгер
    """
    return logging.getLogger(name)


class DiscordLogHandler(logging.Handler):
    """Обработчик для отправки критических логов в Discord канал"""
    
    def __init__(self, bot, channel_id: int, min_level: int = logging.ERROR):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id
        self.setLevel(min_level)
        
    def emit(self, record):
        """Отправка лога в Discord"""
        try:
            # Форматируем сообщение
            log_entry = self.format(record)
            
            # Определяем эмодзи по уровню
            emoji = {
                logging.WARNING: "⚠️",
                logging.ERROR: "❌",
                logging.CRITICAL: "🚨"
            }.get(record.levelno, "📝")
            
            # Создаём embed
            embed = {
                "title": f"{emoji} {record.levelname}",
                "description": f"```{log_entry[:1900]}```",
                "color": {
                    logging.WARNING: 0xFFA500,  # Оранжевый
                    logging.ERROR: 0xFF0000,    # Красный
                    logging.CRITICAL: 0x8B0000  # Тёмно-красный
                }.get(record.levelno, 0x808080),
                "timestamp": datetime.utcnow().isoformat(),
                "fields": [
                    {"name": "Logger", "value": record.name, "inline": True},
                    {"name": "Function", "value": record.funcName, "inline": True},
                    {"name": "Line", "value": str(record.lineno), "inline": True}
                ]
            }
            
            # Отправляем асинхронно
            self.bot.loop.create_task(self._send_to_discord(embed))
            
        except Exception:
            self.handleError(record)
            
    async def _send_to_discord(self, embed_data):
        """Асинхронная отправка в Discord"""
        try:
            channel = self.bot.get_channel(self.channel_id)
            if channel:
                embed = self.bot.discord.Embed.from_dict(embed_data)
                await channel.send(embed=embed)
        except Exception as e:
            print(f"Ошибка отправки лога в Discord: {e}")


def clean_old_logs(log_dir: Path, days_to_keep: int = 30):
    """
    Очистка старых логов
    
    Args:
        log_dir: Директория с логами
        days_to_keep: Сколько дней хранить логи
    """
    if not log_dir.exists():
        return
        
    cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
    
    for log_file in log_dir.glob("*.log*"):
        if log_file.stat().st_mtime < cutoff_date:
            try:
                log_file.unlink()
                logging.info(f"Удалён старый лог: {log_file}")
            except Exception as e:
                logging.error(f"Ошибка удаления лога {log_file}: {e}") 