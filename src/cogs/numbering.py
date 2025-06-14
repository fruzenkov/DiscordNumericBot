# -*- coding: utf-8 -*-
"""
Модуль команд нумерации участников
"""

import discord
from discord.ext import commands
from discord import app_commands
import random
import re
from typing import List, Optional
import logging

from ..utils.permissions import requires_host_permission
from ..utils.logger import get_logger

logger = get_logger(__name__)


class NumberingCog(commands.Cog, name="Нумерация"):
    """Команды для нумерации участников в голосовых каналах"""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_sessions = {}  # guild_id: session_id
        
    def remove_numbers(self, nickname: str) -> str:
        """
        Удаление номеров из никнейма
        
        Args:
            nickname: Никнейм для обработки
            
        Returns:
            Очищенный никнейм
        """
        for pattern in self.bot.config.number_formats:
            nickname = re.sub(pattern, '', nickname)
        return nickname.strip()
        
    @commands.command(name="number", aliases=["номера", "num"])
    @requires_host_permission()
    async def number_participants(self, ctx: commands.Context):
        """
        Присвоить случайные номера участникам голосового канала
        
        Использование: !number
        """
        # Проверяем, что пользователь в голосовом канале
        if not ctx.author.voice:
            await ctx.send("❌ Вы должны находиться в голосовом канале!")
            return
            
        voice_channel = ctx.author.voice.channel
        
        # Получаем участников (исключая автора команды)
        members = [m for m in voice_channel.members if m != ctx.author]
        
        if not members:
            await ctx.send("❌ В канале нет других участников для нумерации!")
            return
            
        # Логируем действие
        await self.bot.db.log_action(
            ctx.guild.id, 
            ctx.author.id, 
            "number_command", 
            f"Канал: {voice_channel.name}, Участников: {len(members)}"
        )
        
        # Сохраняем ведущего
        host_id = await self.bot.db.add_or_update_host(
            ctx.guild.id, 
            ctx.author.id, 
            ctx.author.display_name
        )
        
        # Начинаем сессию
        session_id = await self.bot.db.start_numbering_session(
            ctx.guild.id,
            voice_channel.id,
            host_id,
            len(members)
        )
        self.active_sessions[ctx.guild.id] = session_id
        
        # Генерируем случайные номера
        numbers = list(range(1, len(members) + 1))
        random.shuffle(numbers)
        
        # Результаты
        success_count = 0
        failed_members = []
        results = []
        
        # Присваиваем номера
        for member, number in zip(members, numbers):
            old_nick = member.display_name
            clean_nick = self.remove_numbers(old_nick)
            new_nick = f"{number:02d}. {clean_nick}"
            
            try:
                await member.edit(nick=new_nick)
                success_count += 1
                results.append(f"✅ {old_nick} → **{new_nick}**")
                logger.info(f"Переименован: {old_nick} → {new_nick}")
            except discord.Forbidden:
                failed_members.append((member, new_nick))
                results.append(f"❌ {old_nick} → **{new_nick}** *(недостаточно прав)*")
                logger.warning(f"Не удалось переименовать {member.name}: недостаточно прав")
            except Exception as e:
                failed_members.append((member, new_nick))
                results.append(f"❌ {old_nick} → **{new_nick}** *(ошибка)*")
                logger.error(f"Ошибка переименования {member.name}: {e}")
                
        # Создаём embed с результатами
        embed = discord.Embed(
            title="🎲 Результаты нумерации",
            description=f"Канал: **{voice_channel.name}**\n"
                       f"Ведущий: {ctx.author.mention}\n"
                       f"Участников: **{len(members)}**",
            color=discord.Color.green() if not failed_members else discord.Color.orange()
        )
        
        # Добавляем результаты
        if results:
            # Разбиваем на части, если слишком длинно
            result_text = "\n".join(results[:10])
            if len(results) > 10:
                result_text += f"\n*...и ещё {len(results) - 10} участников*"
            embed.add_field(
                name=f"Успешно: {success_count}/{len(members)}",
                value=result_text,
                inline=False
            )
            
        # Если есть неудачные попытки
        if failed_members:
            failed_text = []
            for member, new_nick in failed_members[:5]:
                failed_text.append(f"• {member.mention} → **{new_nick}**")
            if len(failed_members) > 5:
                failed_text.append(f"*...и ещё {len(failed_members) - 5} участников*")
                
            embed.add_field(
                name="⚠️ Требуется ручное переименование:",
                value="\n".join(failed_text),
                inline=False
            )
            
        embed.set_footer(text=f"Сессия #{session_id}")
        
        await ctx.send(embed=embed)
        
    @commands.command(name="clear", aliases=["очистить", "удалить"])
    @requires_host_permission()
    async def clear_numbers(self, ctx: commands.Context):
        """
        Удалить номера из никнеймов участников
        
        Использование: !clear
        """
        # Проверяем, что пользователь в голосовом канале
        if not ctx.author.voice:
            await ctx.send("❌ Вы должны находиться в голосовом канале!")
            return
            
        voice_channel = ctx.author.voice.channel
        members = voice_channel.members
        
        # Логируем действие
        await self.bot.db.log_action(
            ctx.guild.id, 
            ctx.author.id, 
            "clear_command", 
            f"Канал: {voice_channel.name}"
        )
        
        # Завершаем активную сессию
        if ctx.guild.id in self.active_sessions:
            await self.bot.db.end_numbering_session(self.active_sessions[ctx.guild.id])
            del self.active_sessions[ctx.guild.id]
            
        # Результаты
        success_count = 0
        changed_count = 0
        
        for member in members:
            old_nick = member.display_name
            new_nick = self.remove_numbers(old_nick)
            
            # Пропускаем, если ничего не изменилось
            if old_nick == new_nick:
                continue
                
            changed_count += 1
            
            try:
                await member.edit(nick=new_nick if new_nick else member.name)
                success_count += 1
                logger.info(f"Очищен никнейм: {old_nick} → {new_nick}")
            except discord.Forbidden:
                logger.warning(f"Не удалось очистить никнейм {member.name}: недостаточно прав")
            except Exception as e:
                logger.error(f"Ошибка очистки никнейма {member.name}: {e}")
                
        # Создаём embed с результатами
        embed = discord.Embed(
            title="🧹 Очистка номеров",
            description=f"Канал: **{voice_channel.name}**",
            color=discord.Color.green() if success_count == changed_count else discord.Color.orange()
        )
        
        embed.add_field(
            name="Результат",
            value=f"Обработано: **{len(members)}** участников\n"
                  f"Изменено: **{success_count}/{changed_count}** никнеймов",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
    @app_commands.command(name="number", description="Присвоить случайные номера участникам канала")
    @app_commands.check(lambda interaction: True)  # Проверка прав будет внутри команды
    async def slash_number(self, interaction: discord.Interaction):
        """Slash-команда для нумерации"""
        # Создаём фейковый контекст для использования существующей логики
        ctx = await self.bot.get_context(interaction)
        
        # Проверяем права
        if not await self.bot.permission_system.check_host_permissions(ctx):
            await interaction.response.send_message(
                "❌ У вас недостаточно прав для использования этой команды!",
                ephemeral=True
            )
            return
            
        # Отправляем начальный ответ
        await interaction.response.defer()
        
        # Используем существующую команду
        await self.number_participants(ctx)
        
    @app_commands.command(name="clear", description="Удалить номера из никнеймов")
    @app_commands.check(lambda interaction: True)
    async def slash_clear(self, interaction: discord.Interaction):
        """Slash-команда для очистки номеров"""
        ctx = await self.bot.get_context(interaction)
        
        if not await self.bot.permission_system.check_host_permissions(ctx):
            await interaction.response.send_message(
                "❌ У вас недостаточно прав для использования этой команды!",
                ephemeral=True
            )
            return
            
        await interaction.response.defer()
        await self.clear_numbers(ctx)
        
    @commands.command(name="hosts", aliases=["ведущие", "хосты"])
    async def list_hosts(self, ctx: commands.Context):
        """
        Показать список ведущих сервера
        
        Использование: !hosts
        """
        hosts = await self.bot.db.get_active_hosts(ctx.guild.id)
        
        if not hosts:
            await ctx.send("📋 На этом сервере пока нет сохранённых ведущих.")
            return
            
        embed = discord.Embed(
            title="👥 Ведущие сервера",
            description=f"Всего ведущих: **{len(hosts)}**",
            color=discord.Color.blue()
        )
        
        # Сортируем по количеству сессий
        hosts.sort(key=lambda h: h['sessions_count'], reverse=True)
        
        host_list = []
        for i, host in enumerate(hosts[:10], 1):
            try:
                user = self.bot.get_user(host['user_id'])
                if not user:
                    user = await self.bot.fetch_user(host['user_id'])
                name = user.mention if user else f"ID: {host['user_id']}"
            except:
                name = f"ID: {host['user_id']}"
                
            sessions = host['sessions_count']
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            
            host_list.append(
                f"{emoji} {name} - **{sessions}** {'сессия' if sessions == 1 else 'сессий'}"
            )
            
        embed.add_field(
            name="Топ ведущих",
            value="\n".join(host_list),
            inline=False
        )
        
        await ctx.send(embed=embed)


async def setup(bot):
    """Подключение модуля к боту"""
    await bot.add_cog(NumberingCog(bot)) 