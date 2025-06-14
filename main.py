#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Discord Numeric Bot - Продвинутый бот для нумерации участников
Author: Your Name
GitHub: https://github.com/yourusername/DiscordNumericBot
"""

import asyncio
import discord
from discord.ext import commands
import logging
import sys
from pathlib import Path

# Добавляем корневую папку в путь
sys.path.insert(0, str(Path(__file__).parent))

from src.bot import NumericBot
from src.config import Config
from src.utils.logger import setup_logger

# Настройка базового логирования
logger = setup_logger('main')


async def main():
    """Главная функция запуска бота"""
    try:
        # Загружаем конфигурацию
        config = Config()
        
        # Проверяем наличие токена
        if not config.token:
            logger.error("Токен бота не найден! Проверьте файл .env или переменные окружения.")
            return
        
        # Инициализируем бота
        bot = NumericBot(config)
        
        # Запускаем бота
        logger.info("Запуск Discord Numeric Bot...")
        await bot.start(config.token)
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки...")
    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")
    finally:
        if 'bot' in locals():
            await bot.close()
            logger.info("Бот остановлен.")


if __name__ == "__main__":
    # Запускаем асинхронную главную функцию
    asyncio.run(main()) 