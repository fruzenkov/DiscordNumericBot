# -*- coding: utf-8 -*-
"""
Система управления правами доступа
"""

import discord
from discord.ext import commands
from typing import Union, List, Optional
import logging

logger = logging.getLogger(__name__)


class PermissionSystem:
    """Система управления правами доступа"""
    
    def __init__(self, database, config):
        """
        Инициализация системы прав
        
        Args:
            database: Объект базы данных
            config: Объект конфигурации
        """
        self.db = database
        self.config = config
        
    async def check_permissions(self, ctx: commands.Context) -> bool:
        """
        Проверка прав пользователя
        
        Args:
            ctx: Контекст команды
            
        Returns:
            True если у пользователя есть права
        """
        user_id = ctx.author.id
        guild_id = ctx.guild.id if ctx.guild else None
        
        # Глобальные администраторы
        if user_id in self.config.global_admins:
            logger.debug(f"Пользователь {user_id} - глобальный администратор")
            return True
            
        # Владелец сервера
        if ctx.guild and ctx.author == ctx.guild.owner:
            logger.debug(f"Пользователь {user_id} - владелец сервера")
            return True
            
        # Администратор сервера
        if ctx.author.guild_permissions.administrator:
            logger.debug(f"Пользователь {user_id} - администратор сервера")
            return True
            
        # Проверка в базе данных
        if guild_id:
            authorized_users = await self.db.get_authorized_users(guild_id)
            for user in authorized_users:
                if user['user_id'] == user_id:
                    logger.debug(f"Пользователь {user_id} авторизован с ролью {user['role']}")
                    return True
                    
        # Проверка настроек сервера
        if guild_id:
            settings = await self.db.get_guild_settings(guild_id)
            
            # Проверка по никнейму
            required_nickname = settings.get('required_nickname')
            if required_nickname and required_nickname.lower() in ctx.author.display_name.lower():
                logger.debug(f"Пользователь {user_id} имеет требуемый никнейм")
                return True
                
            # Проверка по ролям
            allowed_roles = settings.get('allowed_roles', [])
            user_role_ids = [role.id for role in ctx.author.roles]
            if any(role_id in allowed_roles for role_id in user_role_ids):
                logger.debug(f"Пользователь {user_id} имеет разрешённую роль")
                return True
                
        logger.debug(f"Пользователь {user_id} не имеет прав")
        return False
        
    async def check_host_permissions(self, ctx: commands.Context) -> bool:
        """
        Проверка, может ли пользователь быть ведущим
        
        Args:
            ctx: Контекст команды
            
        Returns:
            True если пользователь может быть ведущим
        """
        # Сначала базовая проверка
        if not await self.check_permissions(ctx):
            return False
            
        # Дополнительные проверки для ведущих
        if ctx.guild:
            settings = await self.db.get_guild_settings(ctx.guild.id)
            
            # Проверка, включена ли функция автосохранения ведущих
            if not self.config.features.get('auto_save_hosts', True):
                return True
                
            # Проверка специальных прав ведущего
            authorized_users = await self.db.get_authorized_users(ctx.guild.id)
            for user in authorized_users:
                if user['user_id'] == ctx.author.id and user['role'] in ['admin', 'moderator', 'host']:
                    return True
                    
        return True
        
    def is_admin(self, member: discord.Member) -> bool:
        """
        Проверка, является ли пользователь администратором
        
        Args:
            member: Участник сервера
            
        Returns:
            True если администратор
        """
        return (
            member.id in self.config.global_admins or
            member.guild_permissions.administrator or
            member == member.guild.owner
        )
        
    async def add_authorized_user(self, guild_id: int, user_id: int, 
                                role: str, added_by: int) -> bool:
        """
        Добавить авторизованного пользователя
        
        Args:
            guild_id: ID сервера
            user_id: ID пользователя
            role: Роль (admin, moderator, host)
            added_by: ID добавившего пользователя
            
        Returns:
            True если успешно добавлен
        """
        try:
            await self.db.add_authorized_user(guild_id, user_id, role, added_by)
            logger.info(f"Пользователь {user_id} добавлен с ролью {role} на сервере {guild_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления авторизованного пользователя: {e}")
            return False
            
    async def remove_authorized_user(self, guild_id: int, user_id: int) -> bool:
        """
        Удалить авторизованного пользователя
        
        Args:
            guild_id: ID сервера
            user_id: ID пользователя
            
        Returns:
            True если успешно удалён
        """
        try:
            await self.db.remove_authorized_user(guild_id, user_id)
            logger.info(f"Пользователь {user_id} удалён из авторизованных на сервере {guild_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления авторизованного пользователя: {e}")
            return False


# Декораторы для проверки прав
def requires_permission():
    """Декоратор для команд, требующих базовые права"""
    async def predicate(ctx: commands.Context) -> bool:
        bot = ctx.bot
        if hasattr(bot, 'permission_system'):
            return await bot.permission_system.check_permissions(ctx)
        return False
    return commands.check(predicate)


def requires_host_permission():
    """Декоратор для команд ведущего"""
    async def predicate(ctx: commands.Context) -> bool:
        bot = ctx.bot
        if hasattr(bot, 'permission_system'):
            return await bot.permission_system.check_host_permissions(ctx)
        return False
    return commands.check(predicate)


def requires_admin():
    """Декоратор для команд администратора"""
    async def predicate(ctx: commands.Context) -> bool:
        bot = ctx.bot
        if hasattr(bot, 'permission_system'):
            return bot.permission_system.is_admin(ctx.author)
        return False
    return commands.check(predicate) 