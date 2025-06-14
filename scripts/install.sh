#!/bin/bash

# Discord Numeric Bot - Профессиональный скрипт установки для Linux
# Этот скрипт автоматически устанавливает бота и настраивает его для запуска
# в качестве системного сервиса под отдельным пользователем.

set -e # Выход при любой ошибке

# --- Переменные ---
BOT_USER="numericbot"
INSTALL_DIR="/opt/DiscordNumericBot"
REPO_URL="https://github.com/fruzenkov/DiscordNumericBot.git"

# --- Цвета для вывода ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# --- Функции ---
print_message() {
    echo -e "${2}${1}${NC}"
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# --- Основная логика ---

print_message "Discord Numeric Bot - Установщик v2.0" "$BLUE"
print_message "======================================" "$BLUE"

# 1. Проверка прав root
if [[ $EUID -ne 0 ]]; then
   print_message "Ошибка: Этот скрипт необходимо запускать с правами sudo." "$RED"
   print_message "Пожалуйста, выполните: sudo ./install.sh" "$YELLOW"
   exit 1
fi

# 2. Обновление пакетов и установка зависимостей
print_message "\n-> Шаг 1: Установка системных зависимостей..." "$YELLOW"
apt-get update
apt-get install -y git python3-venv python3-pip

# 3. Создание системного пользователя для бота
print_message "\n-> Шаг 2: Создание системного пользователя '$BOT_USER'..." "$YELLOW"
if ! id -u "$BOT_USER" >/dev/null 2>&1; then
    useradd -r -m -d "/home/$BOT_USER" -s /bin/bash "$BOT_USER"
    print_message "Пользователь '$BOT_USER' успешно создан." "$GREEN"
else
    print_message "Пользователь '$BOT_USER' уже существует." "$GREEN"
fi

# 4. Клонирование или обновление репозитория
print_message "\n-> Шаг 3: Загрузка файлов бота в '$INSTALL_DIR'..." "$YELLOW"
if [ ! -d "$INSTALL_DIR" ]; then
    git clone "$REPO_URL" "$INSTALL_DIR"
    print_message "Репозиторий успешно клонирован." "$GREEN"
else
    # Если папка существует, просто обновляем ее
    cd "$INSTALL_DIR"
    git pull
    print_message "Репозиторий обновлен до последней версии." "$GREEN"
fi
chown -R "$BOT_USER:$BOT_USER" "$INSTALL_DIR"

# 5. Установка зависимостей Python в виртуальном окружении
print_message "\n-> Шаг 4: Настройка Python окружения..." "$YELLOW"
# Выполняем от имени нового пользователя
sudo -u "$BOT_USER" bash << EOF
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
EOF
print_message "Зависимости Python успешно установлены." "$GREEN"

# 6. Создание файла .env
print_message "\n-> Шаг 5: Создание файла конфигурации..." "$YELLOW"
ENV_FILE="$INSTALL_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    cp "$INSTALL_DIR/env.example" "$ENV_FILE"
    chown "$BOT_USER:$BOT_USER" "$ENV_FILE"
    print_message "Файл .env создан. Не забудьте добавить в него токен!" "$GREEN"
else
    print_message "Файл .env уже существует." "$GREEN"
fi

# 7. Создание и установка systemd сервиса
print_message "\n-> Шаг 6: Создание systemd сервиса..." "$YELLOW"
SERVICE_FILE="/etc/systemd/system/discord-numeric-bot.service"
cat > $SERVICE_FILE << EOL
[Unit]
Description=Discord Numeric Bot
After=network.target

[Service]
Type=simple
User=$BOT_USER
Group=$BOT_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

# Перезагружаем демоны и включаем сервис
systemctl daemon-reload
systemctl enable discord-numeric-bot

print_message "Systemd сервис 'discord-numeric-bot' успешно создан и включен!" "$GREEN"

# --- Итоговая информация ---
print_message "\n====================================" "$BLUE"
print_message "Установка почти завершена!" "$GREEN"
print_message "====================================" "$BLUE"
print_message "\nОСТАЛСЯ ВСЕГО ОДИН ШАГ:" "$YELLOW"
print_message "1. Отредактируйте файл конфигурации и добавьте токен вашего бота:" "$NC"
print_message "   sudo nano $ENV_FILE" "$YELLOW"
print_message "\n2. После сохранения файла, запустите бота командой:" "$NC"
print_message "   sudo systemctl start discord-numeric-bot" "$YELLOW"

print_message "\nПолезные команды для управления ботом:" "$BLUE"
print_message "- Проверить статус:   sudo systemctl status discord-numeric-bot" "$NC"
print_message "- Посмотреть логи:    sudo journalctl -u discord-numeric-bot -f" "$NC"
print_message "- Остановить бота:    sudo systemctl stop discord-numeric-bot" "$NC"
print_message "- Перезапустить бота: sudo systemctl restart discord-numeric-bot" "$NC" 