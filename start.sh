#!/bin/bash

echo "🚀 Запуск Time Capsule Bot на Railway..."

# Создаем папки
mkdir -p media

# Запускаем бота в фоне
python3 bot.py &

# Запускаем админ-панель
gunicorn --bind 0.0.0.0:$PORT admin_panel:app &

# Ждем
wait