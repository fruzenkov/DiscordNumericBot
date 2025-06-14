# Discord Numeric Bot 🎲

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![discord.py](https://img.shields.io/badge/discord.py-2.3.0+-blue.svg)](https://pypi.org/project/discord.py/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Продвинутый Discord-бот для автоматической нумерации участников в голосовых каналах.

<!-- TODO: Замените YOUR_BOT_ID на ID вашего бота -->
[Пригласить бота](https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_ID&permissions=268435456&scope=bot%20applications.commands) | <!-- TODO: Укажите ссылку на ваш сервер поддержки -->[Сервер поддержки](https://discord.gg/YOUR_SERVER) | [Документация](https://github.com/fruzenkov/DiscordNumericBot/wiki)

<!-- TODO: Рассмотрите возможность добавить GIF-демонстрацию работы бота -->
<!-- <img src="link_to_your_demo.gif" alt="Демонстрация работы бота" width="600"/> -->

</div>

## 📋 Описание

Discord Numeric Bot - это мощный инструмент для организации мероприятий в Discord. Бот автоматически присваивает случайные номера участникам голосового канала, что идеально подходит для:

- 🎮 Турниров и соревнований
- 🎁 Розыгрышей и лотерей
- 🗳️ Голосований и опросов
- 📊 Организации очередей
- 🎯 Командных игр

## ✨ Особенности

- **🎲 Случайная нумерация** - Справедливое распределение номеров
- **✍️ Кастомизация никнеймов** - Автоматическое добавление и удаление номеров.
- **💾 База данных** - Сохранение истории и статистики (SQLite).
- **👥 Система ведущих** - Отслеживание активности организаторов.
- **🔐 Гибкие права доступа** - Настройка по ролям и администраторам.
- **📊 Подробная статистика** - Аналитика использования.
- **🌐 Мультисерверность** - Работа на множестве серверов одновременно.
- **⚡ Slash-команды** - Современный и удобный интерфейс Discord.
- **📝 Продвинутое логирование** - Детальные логи всех действий с ротацией.
- **🐳 Docker-поддержка** - Готовые файлы для быстрой контейнеризации.

## 🚀 Быстрый старт

### Требования

- Python 3.8 или выше
- pip (менеджер пакетов Python)
- Discord Bot Token

### Установка

1. **Клонируйте репозиторий**
```bash
git clone https://github.com/fruzenkov/DiscordNumericBot.git
cd DiscordNumericBot
```

2. **Создайте виртуальное окружение** (рекомендуется)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Установите зависимости**
```bash
pip install -r requirements.txt
```

4. **Настройте бота**
```bash
# Скопируйте пример конфигурации
cp env.example .env

# Отредактируйте .env и добавьте свой токен
# DISCORD_TOKEN=your_bot_token_here
```

5. **Запустите бота**
```bash
python main.py
```

## 📚 Команды

### 🎲 Основные команды

| Команда | Описание | Пример |
|---------|----------|--------|
| `!number` | Присвоить случайные номера участникам | `!number` |
| `!clear` | Удалить номера из никнеймов | `!clear` |
| `!hosts` | Показать список ведущих | `!hosts` |

### 🛡️ Административные команды

| Команда | Описание | Пример |
|---------|----------|--------|
| `!authorize @user [role]` | Добавить пользователя в авторизованные | `!authorize @John host` |
| `!unauthorize @user` | Удалить из авторизованных | `!unauthorize @John` |
| `!authorized` | Список авторизованных пользователей | `!authorized` |
| `!setnick текст` | Установить обязательную часть никнейма | `!setnick [MOD]` |
| `!setrole @role` | Добавить роль с доступом к командам | `!setrole @Moderator` |
| `!logs [число]` | Показать последние действия | `!logs 20` |

### ⚙️ Команды настроек

| Команда | Описание | Пример |
|---------|----------|--------|
| `!settings` | Показать настройки сервера | `!settings` |
| `!export` | Экспортировать настройки в файл | `!export` |
| `!stats` | Статистика сервера | `!stats` |
| `!info` | Информация о боте | `!info` |
| `!ping` | Проверить задержку | `!ping` |

## 🔧 Конфигурация

### Переменные окружения (.env)

```env
# Основные настройки
DISCORD_TOKEN=your_bot_token_here
BOT_PREFIX=!
SYNC_COMMANDS_ON_START=true

# База данных
DATABASE_PATH=data/bot.db

# Логирование
LOGS_DIR=logs
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=30

# Администраторы
GLOBAL_ADMINS=123456789,987654321
```

### Форматы номеров

Бот поддерживает различные форматы нумерации:
- `01. Имя` - Стандартный формат
- `01 || Имя` - С разделителем
- `[01] Имя` - В квадратных скобках
- `01 - Имя` - С тире

## 🐳 Docker

### Использование Docker

```bash
# Сборка образа
docker build -t discord-numeric-bot .

# Запуск контейнера
docker run -d \
  --name numeric-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  discord-numeric-bot
```

### Docker Compose

```yaml
version: '3.8'

services:
  bot:
    build: .
    container_name: numeric-bot
    env_file: .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
```

## 🚀 Развертывание на VPS

### Systemd Service (Linux)

1. Создайте файл сервиса:
```bash
sudo nano /etc/systemd/system/discord-numeric-bot.service
```

2. Добавьте конфигурацию:
```ini
[Unit]
Description=Discord Numeric Bot
After=network.target

[Service]
Type=simple
# TODO: Замените 'your_user' на вашего пользователя
User=your_user
# TODO: Укажите корректный путь к проекту
WorkingDirectory=/home/your_user/DiscordNumericBot
# TODO: Укажите корректный путь к виртуальному окружению
Environment="PATH=/home/your_user/DiscordNumericBot/venv/bin"
ExecStart=/home/your_user/DiscordNumericBot/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

3. Запустите сервис:
```bash
sudo systemctl enable discord-numeric-bot
sudo systemctl start discord-numeric-bot
```

## 📊 База данных

Бот использует SQLite для хранения данных. Структура БД:

- **guilds** - Информация о серверах
- **authorized_users** - Авторизованные пользователи
- **hosts** - Ведущие мероприятий
- **numbering_sessions** - История сессий нумерации
- **action_logs** - Логи действий

## 🛡️ Безопасность

- Никогда не публикуйте токен бота
- Используйте `.env` файл для хранения секретов
- Регулярно обновляйте зависимости
- Ограничивайте права бота необходимым минимумом
- Делайте резервные копии базы данных

## 🤝 Вклад в проект

Мы приветствуем любой вклад в развитие проекта!

1. Форкните репозиторий
2. Создайте ветку для фичи (`git checkout -b feature/AmazingFeature`)
3. Сделайте коммит (`git commit -m 'Add some AmazingFeature'`)
4. Запушьте изменения (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## 📝 Лицензия

Этот проект распространяется под лицензией MIT. Смотрите файл [LICENSE](LICENSE) для подробностей.

## 👨‍💻 Автор

**fruzenkov**
- GitHub: [@fruzenkov](https://github.com/fruzenkov)
<!-- TODO: Укажите ваш Discord-тег -->
- Discord: YourName#0000

## 🙏 Благодарности

- [discord.py](https://github.com/Rapptz/discord.py) - Библиотека для Discord API
- Сообществу Python за бесценные знания и инструменты.

---

<div align="center">
Сделано с ❤️ для Discord сообщества
</div> 