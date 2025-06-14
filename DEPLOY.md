# 🚀 Руководство по развертыванию на VPS

## 📋 Требования к VPS

- **ОС**: Ubuntu 20.04+ / Debian 10+ / CentOS 8+
- **RAM**: Минимум 512MB (рекомендуется 1GB)
- **CPU**: 1 vCPU
- **Диск**: 10GB свободного места
- **Python**: 3.8 или выше

## 🔧 Подготовка VPS

### 1. Обновление системы

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
```

### 2. Установка необходимых пакетов

```bash
# Ubuntu/Debian
sudo apt install -y python3 python3-pip python3-venv git

# CentOS/RHEL
sudo yum install -y python3 python3-pip git
```

## 📦 Установка бота

### 1. Клонирование репозитория

```bash
cd ~
git clone https://github.com/yourusername/DiscordNumericBot.git
cd DiscordNumericBot
```

### 2. Запуск скрипта установки

```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

### 3. Настройка токена

```bash
nano .env
# Добавьте ваш токен:
# DISCORD_TOKEN=ваш_токен_здесь
```

### 4. Настройка глобальных администраторов

Отредактируйте файл `.env` и добавьте Discord ID администраторов:

```bash
GLOBAL_ADMINS=559751322786725889,557993122869542932
```

## 🐳 Установка через Docker (альтернативный метод)

### 1. Установка Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### 2. Установка Docker Compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 3. Запуск через Docker Compose

```bash
# Создайте .env файл с токеном
cp env.example .env
nano .env

# Запустите контейнеры
docker-compose up -d
```

## 🔄 Автозапуск через systemd

### 1. Копирование файла сервиса

```bash
sudo cp discord-numeric-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### 2. Включение автозапуска

```bash
sudo systemctl enable discord-numeric-bot
sudo systemctl start discord-numeric-bot
```

### 3. Проверка статуса

```bash
sudo systemctl status discord-numeric-bot
```

## 📊 Мониторинг

### Просмотр логов

```bash
# Системные логи
sudo journalctl -u discord-numeric-bot -f

# Логи бота
tail -f logs/bot_$(date +%Y-%m-%d).log
```

### Проверка использования ресурсов

```bash
# CPU и память
htop

# Дисковое пространство
df -h

# Размер папок
du -sh data/ logs/
```

## 🔄 Обновление бота

### Автоматическое обновление

```bash
./update.sh
```

### Ручное обновление

```bash
# Остановка бота
sudo systemctl stop discord-numeric-bot

# Получение обновлений
git pull

# Обновление зависимостей
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Запуск бота
sudo systemctl start discord-numeric-bot
```

## 💾 Резервное копирование

### Автоматическое резервное копирование

```bash
# Добавьте в crontab
crontab -e

# Ежедневное резервное копирование в 3:00
0 3 * * * /home/user/DiscordNumericBot/backup.sh
```

### Ручное резервное копирование

```bash
./backup.sh
```

### Восстановление из резервной копии

```bash
# Остановите бота
sudo systemctl stop discord-numeric-bot

# Восстановите данные
tar -xzf backups/backup_20240101_030000.tar.gz

# Запустите бота
sudo systemctl start discord-numeric-bot
```

## 🔒 Безопасность

### 1. Настройка файрвола

```bash
# UFW (Ubuntu/Debian)
sudo ufw allow ssh
sudo ufw enable

# Firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

### 2. Создание отдельного пользователя

```bash
sudo useradd -m -s /bin/bash botuser
sudo su - botuser
# Выполните установку от имени этого пользователя
```

### 3. Ограничение прав доступа

```bash
chmod 600 .env
chmod 700 data/
```

## 🐛 Устранение неполадок

### Бот не запускается

1. Проверьте токен в `.env`
2. Проверьте логи: `sudo journalctl -u discord-numeric-bot -n 50`
3. Убедитесь, что все зависимости установлены

### Ошибки с правами доступа

```bash
# Исправление прав
sudo chown -R $USER:$USER /path/to/DiscordNumericBot
chmod -R 755 /path/to/DiscordNumericBot
chmod 600 .env
```

### Проблемы с подключением

1. Проверьте интернет-соединение
2. Убедитесь, что Discord API доступен
3. Проверьте правильность токена

## 📞 Поддержка

- **Discord сервер**: [Присоединиться](https://discord.gg/YOUR_SERVER)
- **GitHub Issues**: [Создать issue](https://github.com/yourusername/DiscordNumericBot/issues)
- **Email**: support@example.com

## 📝 Чек-лист развертывания

- [ ] VPS соответствует минимальным требованиям
- [ ] Python 3.8+ установлен
- [ ] Репозиторий склонирован
- [ ] Виртуальное окружение создано
- [ ] Зависимости установлены
- [ ] Токен бота добавлен в `.env`
- [ ] Глобальные администраторы настроены
- [ ] Systemd сервис установлен и запущен
- [ ] Автозапуск включен
- [ ] Резервное копирование настроено
- [ ] Безопасность настроена

---

<div align="center">
Удачного развертывания! 🎉
</div> 