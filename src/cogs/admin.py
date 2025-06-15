# -*- coding: utf-8 -*-
"""
Модуль административных команд
"""

import discord
from discord.ext import commands
from discord import app_commands
import json
from typing import Optional, Union
import logging

from ..utils.permissions import requires_admin
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AdminCog(commands.Cog, name="Администрирование"):
    """Административные команды для управления ботом"""
    
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="authorize", aliases=["auth", "добавить"])
    @requires_admin()
    async def authorize_user(self, ctx: commands.Context, 
                           member: discord.Member, 
                           role: str = "host"):
        """
        Добавить пользователя в список авторизованных
        
        Использование: !authorize @user [role]
        Роли: admin, moderator, host (по умолчанию)
        """
        valid_roles = ["admin", "moderator", "host"]
        if role.lower() not in valid_roles:
            await ctx.send(f"❌ Неверная роль! Доступные роли: {', '.join(valid_roles)}")
            return
            
        # Добавляем пользователя
        success = await self.bot.permission_system.add_authorized_user(
            ctx.guild.id,
            member.id,
            role.lower(),
            ctx.author.id
        )
        
        if success:
            # Логируем действие
            await self.bot.db.log_action(
                ctx.guild.id,
                ctx.author.id,
                "authorize_user",
                f"Добавлен {member.name} с ролью {role}"
            )
            
            embed = discord.Embed(
                title="✅ Пользователь авторизован",
                description=f"{member.mention} добавлен с ролью **{role}**",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Ошибка при добавлении пользователя!")
            
    @commands.command(name="unauthorize", aliases=["unauth", "удалить_автор"])
    @requires_admin()
    async def unauthorize_user(self, ctx: commands.Context, member: discord.Member):
        """
        Удалить пользователя из списка авторизованных
        
        Использование: !unauthorize @user
        """
        success = await self.bot.permission_system.remove_authorized_user(
            ctx.guild.id,
            member.id
        )
        
        if success:
            # Логируем действие
            await self.bot.db.log_action(
                ctx.guild.id,
                ctx.author.id,
                "unauthorize_user",
                f"Удалён {member.name}"
            )
            
            embed = discord.Embed(
                title="✅ Пользователь удалён",
                description=f"{member.mention} удалён из списка авторизованных",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Ошибка при удалении пользователя!")
            
    @commands.command(name="authorized", aliases=["authlist", "список"])
    @requires_admin()
    async def list_authorized(self, ctx: commands.Context):
        """
        Показать список авторизованных пользователей
        
        Использование: !authorized
        """
        users = await self.bot.db.get_authorized_users(ctx.guild.id)
        
        if not users:
            await ctx.send("📋 На этом сервере нет авторизованных пользователей.")
            return
            
        embed = discord.Embed(
            title="👤 Авторизованные пользователи",
            description=f"Всего: **{len(users)}**",
            color=discord.Color.blue()
        )
        
        # Группируем по ролям
        by_role = {"admin": [], "moderator": [], "host": []}
        for user in users:
            by_role.get(user['role'], []).append(user)
            
        # Добавляем поля для каждой роли
        role_names = {"admin": "Администраторы", "moderator": "Модераторы", "host": "Ведущие"}
        role_emojis = {"admin": "👑", "moderator": "🛡️", "host": "🎙️"}
        
        for role, role_users in by_role.items():
            if not role_users:
                continue
                
            user_list = []
            for user_data in role_users[:10]:  # Максимум 10
                try:
                    user = self.bot.get_user(user_data['user_id'])
                    if not user:
                        user = await self.bot.fetch_user(user_data['user_id'])
                    name = user.mention if user else f"ID: {user_data['user_id']}"
                except:
                    name = f"ID: {user_data['user_id']}"
                    
                user_list.append(f"• {name}")
                
            if len(role_users) > 10:
                user_list.append(f"*...и ещё {len(role_users) - 10}*")
                
            embed.add_field(
                name=f"{role_emojis[role]} {role_names[role]}",
                value="\n".join(user_list),
                inline=True
            )
            
        await ctx.send(embed=embed)
        
    @commands.command(name="setnick", aliases=["setname", "никнейм"])
    @requires_admin()
    async def set_required_nickname(self, ctx: commands.Context, *, nickname_part: str):
        """
        Установить обязательную часть никнейма для доступа к командам
        
        Использование: !setnick часть_никнейма
        """
        # Получаем текущие настройки
        settings = await self.bot.db.get_guild_settings(ctx.guild.id)
        settings['required_nickname'] = nickname_part
        
        # Сохраняем
        await self.bot.db.update_guild_settings(ctx.guild.id, settings)
        
        # Логируем
        await self.bot.db.log_action(
            ctx.guild.id,
            ctx.author.id,
            "set_required_nickname",
            f"Установлено: {nickname_part}"
        )
        
        embed = discord.Embed(
            title="✅ Настройка обновлена",
            description=f"Обязательная часть никнейма: **{nickname_part}**\n"
                       f"Теперь пользователи с этим текстом в нике смогут использовать команды.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        
    @commands.command(name="removenick", aliases=["delnick", "удалитьник"])
    @requires_admin()
    async def remove_required_nickname(self, ctx: commands.Context):
        """
        Удалить требование к никнейму
        
        Использование: !removenick
        """
        settings = await self.bot.db.get_guild_settings(ctx.guild.id)
        if 'required_nickname' in settings:
            del settings['required_nickname']
            await self.bot.db.update_guild_settings(ctx.guild.id, settings)
            
        await ctx.send("✅ Требование к никнейму удалено.")
        
    @commands.command(name="setrole", aliases=["роль"])
    @requires_admin()
    async def add_allowed_role(self, ctx: commands.Context, role: discord.Role):
        """
        Добавить роль, которая может использовать команды
        
        Использование: !setrole @role
        """
        settings = await self.bot.db.get_guild_settings(ctx.guild.id)
        allowed_roles = settings.get('allowed_roles', [])
        
        if role.id in allowed_roles:
            await ctx.send(f"❌ Роль {role.mention} уже в списке разрешённых!")
            return
            
        allowed_roles.append(role.id)
        settings['allowed_roles'] = allowed_roles
        await self.bot.db.update_guild_settings(ctx.guild.id, settings)
        
        # Логируем
        await self.bot.db.log_action(
            ctx.guild.id,
            ctx.author.id,
            "add_allowed_role",
            f"Добавлена роль: {role.name}"
        )
        
        embed = discord.Embed(
            title="✅ Роль добавлена",
            description=f"Роль {role.mention} теперь может использовать команды бота.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        
    @commands.command(name="removerole", aliases=["удалитьроль"])
    @requires_admin()
    async def remove_allowed_role(self, ctx: commands.Context, role: discord.Role):
        """
        Удалить роль из списка разрешённых
        
        Использование: !removerole @role
        """
        settings = await self.bot.db.get_guild_settings(ctx.guild.id)
        allowed_roles = settings.get('allowed_roles', [])
        
        if role.id not in allowed_roles:
            await ctx.send(f"❌ Роль {role.mention} не в списке разрешённых!")
            return
            
        allowed_roles.remove(role.id)
        settings['allowed_roles'] = allowed_roles
        await self.bot.db.update_guild_settings(ctx.guild.id, settings)
        
        embed = discord.Embed(
            title="✅ Роль удалена",
            description=f"Роль {role.mention} больше не может использовать команды бота.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        
    @commands.command(name="logs", aliases=["логи", "история"])
    @requires_admin()
    async def show_logs(self, ctx: commands.Context, limit: int = 20):
        """
        Показать последние действия на сервере
        
        Использование: !logs [количество]
        """
        if limit > 50:
            limit = 50
        elif limit < 1:
            limit = 1
            
        logs = await self.bot.db.get_recent_logs(ctx.guild.id, limit)
        
        if not logs:
            await ctx.send("📋 Нет записей в логах.")
            return
            
        embed = discord.Embed(
            title="📜 История действий",
            description=f"Последние {len(logs)} записей",
            color=discord.Color.blue()
        )
        
        log_text = []
        for log in logs[:10]:  # Максимум 10 в embed
            try:
                user = self.bot.get_user(log['user_id'])
                if not user:
                    user = await self.bot.fetch_user(log['user_id'])
                username = user.name if user else f"ID:{log['user_id']}"
            except:
                username = f"ID:{log['user_id']}"
                
            timestamp = log['timestamp'].split('.')[0]  # Убираем миллисекунды
            action = log['action'].replace('_', ' ').title()
            
            log_text.append(f"`{timestamp}` | **{username}** | {action}")
            if log['details']:
                log_text.append(f"↳ {log['details']}")
                
        embed.description = "\n".join(log_text)
        
        if len(logs) > 10:
            embed.set_footer(text=f"Показаны первые 10 из {len(logs)} записей")
            
        await ctx.send(embed=embed)
        
    @commands.command(name="stats", aliases=["статистика", "стат"])
    async def show_stats(self, ctx: commands.Context):
        """
        Показать статистику сервера
        
        Использование: !stats
        """
        stats = await self.bot.db.get_statistics(ctx.guild.id)
        
        embed = discord.Embed(
            title="📊 Статистика сервера",
            description=ctx.guild.name,
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📈 Общие данные",
            value=f"Сессий проведено: **{stats['total_sessions']}**\n"
                  f"Активных ведущих: **{stats['active_hosts']}**",
            inline=False
        )
        
        if stats['top_hosts']:
            top_text = []
            for i, host in enumerate(stats['top_hosts'], 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                sessions = host['sessions_count']
                top_text.append(
                    f"{emoji} **{host['nickname']}** - {sessions} {'сессия' if sessions == 1 else 'сессий'}"
                )
                
            embed.add_field(
                name="🏆 Топ ведущих",
                value="\n".join(top_text),
                inline=False
            )
            
        # Информация о боте
        embed.add_field(
            name="ℹ️ О боте",
            value=f"Версия: **{self.bot.__class__.__module__.split('.')[0]} v2.0**\n"
                  f"Серверов: **{len(self.bot.guilds)}**\n"
                  f"Префикс: **{self.bot.config.prefix}**",
            inline=False
        )
        
        await ctx.send(embed=embed)


async def setup(bot):
    """Подключение модуля к боту"""
    await bot.add_cog(AdminCog(bot)) 