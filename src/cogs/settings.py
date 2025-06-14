# -*- coding: utf-8 -*-
"""
Модуль команд настроек
"""

import discord
from discord.ext import commands
import json
import logging
import platform
from datetime import datetime

from ..utils.permissions import requires_permission

logger = logging.getLogger(__name__)


class SettingsCog(commands.Cog, name="Настройки"):
    """Команды для просмотра и управления настройками"""
    
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="settings", aliases=["настройки", "config"])
    @requires_permission()
    async def show_settings(self, ctx: commands.Context):
        """
        Показать текущие настройки сервера
        
        Использование: !settings
        """
        # Получаем настройки
        guild_settings = await self.bot.db.get_guild_settings(ctx.guild.id)
        
        embed = discord.Embed(
            title="⚙️ Настройки сервера",
            description=ctx.guild.name,
            color=discord.Color.blue()
        )
        
        # Основные настройки
        embed.add_field(
            name="🔧 Основные",
            value=f"**Префикс:** `{self.bot.config.prefix}`\n"
                  f"**Язык:** `{guild_settings.get('language', self.bot.config.default_language)}`",
            inline=True
        )
        
        # Права доступа
        access_info = []
        
        # Обязательный никнейм
        required_nick = guild_settings.get('required_nickname')
        if required_nick:
            access_info.append(f"**Никнейм:** содержит `{required_nick}`")
        
        # Разрешённые роли
        allowed_roles = guild_settings.get('allowed_roles', [])
        if allowed_roles:
            role_mentions = []
            for role_id in allowed_roles[:5]:  # Максимум 5
                role = ctx.guild.get_role(role_id)
                if role:
                    role_mentions.append(role.mention)
            if role_mentions:
                access_info.append(f"**Роли:** {', '.join(role_mentions)}")
                if len(allowed_roles) > 5:
                    access_info.append(f"*...и ещё {len(allowed_roles) - 5}*")
                    
        if access_info:
            embed.add_field(
                name="🔐 Доступ",
                value="\n".join(access_info),
                inline=True
            )
        else:
            embed.add_field(
                name="🔐 Доступ",
                value="*Только администраторы*",
                inline=True
            )
            
        # Форматы номеров
        formats = self.bot.config.number_formats
        format_examples = {
            "^\\d+\\.\\s*": "01. Имя",
            "^\\d+\\s*\\|\\|\\s*": "01 || Имя",
            "^\\d+\\s*": "01 Имя",
            "^\\d+\\s*-\\s*": "01 - Имя",
            "^\\[\\d+\\]\\s*": "[01] Имя"
        }
        
        format_list = []
        for pattern in formats[:3]:
            example = format_examples.get(pattern, pattern)
            format_list.append(f"• `{example}`")
        if len(formats) > 3:
            format_list.append(f"*...и ещё {len(formats) - 3}*")
            
        embed.add_field(
            name="🔢 Форматы номеров",
            value="\n".join(format_list) if format_list else "*Стандартные*",
            inline=False
        )
        
        # Функции
        features = self.bot.config.features
        feature_names = {
            "auto_save_hosts": "💾 Автосохранение ведущих",
            "multi_language": "🌐 Мультиязычность",
            "slash_commands": "⚡ Slash-команды",
            "web_dashboard": "🌐 Веб-панель"
        }
        
        enabled_features = []
        disabled_features = []
        
        for feature, enabled in features.items():
            feature_name = feature_names.get(feature, feature)
            if enabled:
                enabled_features.append(f"✅ {feature_name}")
            else:
                disabled_features.append(f"❌ {feature_name}")
                
        features_text = "\n".join(enabled_features + disabled_features)
        embed.add_field(
            name="🎛️ Функции",
            value=features_text if features_text else "*Базовые*",
            inline=False
        )
        
        # Глобальные администраторы
        if self.bot.permission_system.is_admin(ctx.author):
            global_admins = self.bot.config.global_admins
            if global_admins:
                admin_mentions = []
                for admin_id in global_admins[:3]:
                    try:
                        user = self.bot.get_user(admin_id)
                        if not user:
                            user = await self.bot.fetch_user(admin_id)
                        admin_mentions.append(user.mention if user else f"ID:{admin_id}")
                    except:
                        admin_mentions.append(f"ID:{admin_id}")
                        
                admin_text = ", ".join(admin_mentions)
                if len(global_admins) > 3:
                    admin_text += f" *...и ещё {len(global_admins) - 3}*"
                    
                embed.add_field(
                    name="👑 Глобальные администраторы",
                    value=admin_text,
                    inline=False
                )
                
        await ctx.send(embed=embed)
        
    @commands.command(name="export", aliases=["экспорт", "backup"])
    @requires_permission()
    async def export_settings(self, ctx: commands.Context):
        """
        Экспортировать настройки сервера
        
        Использование: !export
        """
        # Получаем все данные
        settings = await self.bot.db.get_guild_settings(ctx.guild.id)
        authorized_users = await self.bot.db.get_authorized_users(ctx.guild.id)
        hosts = await self.bot.db.get_active_hosts(ctx.guild.id)
        
        export_data = {
            "guild_id": ctx.guild.id,
            "guild_name": ctx.guild.name,
            "export_date": discord.utils.utcnow().isoformat(),
            "settings": settings,
            "authorized_users": authorized_users,
            "hosts": hosts
        }
        
        # Создаём JSON
        json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
        
        # Создаём файл
        file = discord.File(
            fp=json_data.encode('utf-8'),
            filename=f"settings_{ctx.guild.id}_{discord.utils.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        embed = discord.Embed(
            title="📤 Экспорт настроек",
            description="Настройки сервера экспортированы в JSON файл.",
            color=discord.Color.green()
        )
        
        # Логируем
        await self.bot.db.log_action(
            ctx.guild.id,
            ctx.author.id,
            "export_settings",
            "Экспортированы настройки сервера"
        )
        
        await ctx.send(embed=embed, file=file)
        
    @commands.command(name="info", aliases=["botinfo", "about"])
    async def info(self, ctx: commands.Context):
        """Показать информацию о боте"""
        embed = discord.Embed(
            title=f"Информация о {self.bot.user.name}",
            description="Продвинутый бот для нумерации участников.",
            color=discord.Color.green()
        )

        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)

        embed.add_field(
            name="📊 Статистика",
            value=f"**Серверов:** {len(self.bot.guilds)}\n"
                  f"**Пользователей:** {len(self.bot.users)}",
            inline=True
        )

        uptime = datetime.utcnow() - self.bot.start_time
        days = uptime.days
        hours, rem = divmod(uptime.seconds, 3600)
        minutes, _ = divmod(rem, 60)
        
        embed.add_field(
            name="⏱️ Аптайм",
            value=f"{days}д {hours}ч {minutes}м",
            inline=True
        )
        
        embed.add_field(
            name="⚙️ Техническая информация",
            value=f"**discord.py:** {discord.__version__}\n"
                  f"**Python:** {platform.python_version()}",
            inline=False
        )

        repo_url = "https://github.com/fruzenkov/DiscordNumericBot"
        embed.add_field(
            name="🔗 Ссылка на GitHub",
            value=f"[Репозиторий]({repo_url})",
            inline=False
        )
        
        embed.set_footer(text=f"Автор: fruzenkov")
        
        await ctx.send(embed=embed)
        
    @commands.command(name="ping", aliases=["пинг"])
    async def ping(self, ctx: commands.Context):
        """
        Проверить задержку бота
        
        Использование: !ping
        """
        # Измеряем задержку сообщения
        import time
        start = time.perf_counter()
        message = await ctx.send("🏓 Измеряю задержку...")
        end = time.perf_counter()
        
        # Задержка API
        api_latency = round(self.bot.latency * 1000)
        
        # Задержка сообщения
        message_latency = round((end - start) * 1000)
        
        # Определяем цвет по задержке
        if api_latency < 100:
            color = discord.Color.green()
            status = "🟢 Отлично"
        elif api_latency < 200:
            color = discord.Color.yellow()
            status = "🟡 Хорошо"
        else:
            color = discord.Color.red()
            status = "🔴 Плохо"
            
        embed = discord.Embed(
            title="🏓 Понг!",
            color=color
        )
        
        embed.add_field(
            name="📡 WebSocket",
            value=f"{api_latency}мс",
            inline=True
        )
        
        embed.add_field(
            name="💬 Сообщение",
            value=f"{message_latency}мс",
            inline=True
        )
        
        embed.add_field(
            name="📊 Статус",
            value=status,
            inline=True
        )
        
        await message.edit(content=None, embed=embed)


async def setup(bot):
    """Подключение модуля к боту"""
    await bot.add_cog(SettingsCog(bot)) 