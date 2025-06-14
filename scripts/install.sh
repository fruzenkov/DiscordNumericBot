#!/bin/bash

# Discord Numeric Bot - Скрипт установки для Linux VPS
# Этот скрипт поможет установить и настроить бота на вашем VPS

set -e  # Выход при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
print_message() {
    echo -e "${2}${1}${NC}"
}

# Функция для проверки команды
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

print_message "Discord Numeric Bot - Установщик v1.0" "$BLUE"
print_message "====================================" "$BLUE"

# Проверка прав
if [[ $EUID -eq 0 ]]; then
   print_message "Не запускайте этот скрипт от имени root!" "$RED"
   exit 1
fi

# Проверка системы
print_message "\nПроверка системы..." "$YELLOW"

# Проверка Python
if ! command_exists python3; then
    print_message "Python3 не установлен. Установите Python 3.8+ и запустите скрипт снова." "$RED"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
print_message "Python версия: $PYTHON_VERSION" "$GREEN"

# Проверка pip
if ! command_exists pip3; then
    print_message "pip3 не установлен. Установите pip3 и запустите скрипт снова." "$RED"
    exit 1
fi

# Установка
print_message "\nНачинаем установку..." "$YELLOW"

# Создание виртуального окружения
if [ ! -d "venv" ]; then
    print_message "Создание виртуального окружения..." "$BLUE"
    python3 -m venv venv
else
    print_message "Виртуальное окружение уже существует" "$GREEN"
fi

# Активация виртуального окружения
source venv/bin/activate

# Обновление pip
print_message "Обновление pip..." "$BLUE"
pip install --upgrade pip

# Установка зависимостей
print_message "Установка зависимостей..." "$BLUE"
pip install -r requirements.txt

# Создание необходимых директорий
print_message "\nСоздание директорий..." "$BLUE"
mkdir -p data logs backups

# Копирование примера конфигурации
if [ ! -f ".env" ]; then
    print_message "Создание файла конфигурации..." "$BLUE"
    cp env.example .env
    print_message "Файл .env создан. Не забудьте добавить токен бота!" "$YELLOW"
else
    print_message "Файл .env уже существует" "$GREEN"
fi

# Создание systemd сервиса
print_message "\nСоздание systemd сервиса..." "$BLUE"

SERVICE_FILE="discord-numeric-bot.service"
cat > $SERVICE_FILE << EOL
[Unit]
Description=Discord Numeric Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(pwd)/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

print_message "Файл сервиса создан: $SERVICE_FILE" "$GREEN"
print_message "Для установки сервиса выполните:" "$YELLOW"
print_message "sudo cp $SERVICE_FILE /etc/systemd/system/" "$YELLOW"
print_message "sudo systemctl daemon-reload" "$YELLOW"
print_message "sudo systemctl enable discord-numeric-bot" "$YELLOW"
print_message "sudo systemctl start discord-numeric-bot" "$YELLOW"

# Создание скрипта обновления
cat > update.sh << 'EOL'
#!/bin/bash
# Скрипт обновления бота

echo "Останавливаем бота..."
sudo systemctl stop discord-numeric-bot

echo "Получаем обновления..."
git pull

echo "Активируем виртуальное окружение..."
source venv/bin/activate

echo "Обновляем зависимости..."
pip install -r requirements.txt --upgrade

echo "Запускаем бота..."
sudo systemctl start discord-numeric-bot

echo "Проверяем статус..."
sudo systemctl status discord-numeric-bot
EOL

chmod +x update.sh
print_message "\nСкрипт обновления создан: update.sh" "$GREEN"

# Создание скрипта резервного копирования
cat > backup.sh << 'EOL'
#!/bin/bash
# Скрипт резервного копирования

BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.tar.gz"

echo "Создание резервной копии..."
mkdir -p $BACKUP_DIR
tar -czf $BACKUP_FILE data/ logs/ .env config.json

echo "Резервная копия создана: $BACKUP_FILE"

# Удаление старых бэкапов (старше 7 дней)
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +7 -delete
echo "Старые резервные копии удалены"
EOL

chmod +x backup.sh
print_message "Скрипт резервного копирования создан: backup.sh" "$GREEN"

# Итоговая информация
print_message "\n====================================" "$BLUE"
print_message "Установка завершена!" "$GREEN"
print_message "====================================" "$BLUE"
print_message "\nДальнейшие шаги:" "$YELLOW"
print_message "1. Отредактируйте .env и добавьте токен бота" "$NC"
print_message "2. Установите systemd сервис (команды выше)" "$NC"
print_message "3. Запустите бота: python main.py" "$NC"
print_message "\nПолезные команды:" "$YELLOW"
print_message "- Проверить статус: sudo systemctl status discord-numeric-bot" "$NC"
print_message "- Посмотреть логи: sudo journalctl -u discord-numeric-bot -f" "$NC"
print_message "- Обновить бота: ./update.sh" "$NC"
print_message "- Создать бэкап: ./backup.sh" "$NC" 