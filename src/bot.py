# -*- coding: utf-8 -*-
"""
Основной класс бота
"""

import discord
from discord.ext import commands
import logging
from typing import Optional
import asyncio
from datetime import datetime

from .config import Config
from .database import Database
from .utils.logger import setup_logger
from .utils.permissions import PermissionSystem
from .cogs.numbering import NumberingCog
from .cogs.admin import AdminCog
from .cogs.settings import SettingsCog

logger = setup_logger('bot')


class NumericBot(commands.Bot):
    """Главный класс Discord бота для нумерации участников"""
    
    def __init__(self, config: Config):
        """
        Инициализация бота
        
        Args:
            config: Объект конфигурации
        """
        # Настройка intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.voice_states = True
        intents.guilds = True
        
        # Инициализация родительского класса
        super().__init__(
            command_prefix=config.prefix,
            intents=intents,
            help_command=self._create_help_command()
        )
        
        self.config = config
        self.db: Optional[Database] = None
        self.permission_system: Optional[PermissionSystem] = None
        self.start_time = datetime.utcnow()
        
    def _create_help_command(self) -> commands.HelpCommand:
        """Создание кастомной команды помощи"""
        help_command = commands.DefaultHelpCommand(
            no_category='Другие команды',
            command_attrs={
                'name': 'help',
                'aliases': ['помощь', 'хелп'],
                'description': 'Показывает это сообщение'
            }
        )
        return help_command
        
    async def setup_hook(self):
        """Настройка бота перед запуском"""
        logger.info("Инициализация компонентов бота...")
        
        # Инициализация базы данных
        self.db = Database(self.config.database_path)
        await self.db.initialize()
        logger.info("База данных инициализирована")
        
        # Инициализация системы прав
        self.permission_system = PermissionSystem(self.db, self.config)
        logger.info("Система прав инициализирована")
        
        # Загрузка модулей (cogs)
        await self.load_cogs()
        
        # Синхронизация команд
        if self.config.sync_commands_on_start:
            await self.sync_commands()
            
    async def load_cogs(self):
        """Загрузка всех модулей бота"""
        cogs = [
            NumberingCog(self),
            AdminCog(self),
            SettingsCog(self)
        ]
        
        for cog in cogs:
            await self.add_cog(cog)
            logger.info(f"Загружен модуль: {cog.__class__.__name__}")
            
    async def sync_commands(self):
        """Синхронизация slash-команд с Discord"""
        try:
            synced = await self.tree.sync()
            logger.info(f"Синхронизировано {len(synced)} команд")
        except Exception as e:
            logger.error(f"Ошибка синхронизации команд: {e}")
            
    async def on_ready(self):
        """Событие готовности бота"""
        logger.info(f"Бот {self.user} готов к работе!")
        logger.info(f"ID бота: {self.user.id}")
        logger.info(f"Количество серверов: {len(self.guilds)}")
        logger.info(f"Префикс команд: {self.config.prefix}")
        
        # Установка статуса
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{len(self.guilds)} серверов | {self.config.prefix}help"
            )
        )
        
    async def on_guild_join(self, guild: discord.Guild):
        """Событие присоединения к новому серверу"""
        logger.info(f"Бот добавлен на сервер: {guild.name} (ID: {guild.id})")
        
        # Создание записи в базе данных для нового сервера
        await self.db.ensure_guild_exists(guild.id)
        
        # Обновление статуса
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{len(self.guilds)} серверов | {self.config.prefix}help"
            )
        )
        
    async def on_guild_remove(self, guild: discord.Guild):
        """Событие удаления с сервера"""
        logger.info(f"Бот удалён с сервера: {guild.name} (ID: {guild.id})")
        
        # Обновление статуса
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{len(self.guilds)} серверов | {self.config.prefix}help"
            )
        )
        
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Обработка ошибок команд"""
        if isinstance(error, commands.CommandNotFound):
            return
            
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Отсутствует обязательный аргумент: `{error.param.name}`")
            
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Неверный аргумент: {error}")
            
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("❌ У вас недостаточно прав для выполнения этой команды.")
            
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏱️ Команда на перезарядке. Попробуйте через {error.retry_after:.1f} сек.")
            
        else:
            logger.error(f"Ошибка в команде {ctx.command}: {error}", exc_info=error)
            await ctx.send("❌ Произошла неизвестная ошибка. Администраторы уведомлены.")
            
    async def close(self):
        """Корректное закрытие бота"""
        logger.info("Закрытие соединений...")
        
        # Закрытие базы данных
        if self.db:
            await self.db.close()
            
        # Вызов родительского метода закрытия
        await super().close() 