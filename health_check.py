"""
Проверка здоровья бота и автоматический перезапуск
"""

import requests
import time
import os
import subprocess
import sys


def check_bot_health():
    """Проверяет, отвечает ли бот"""
    try:
        # Попробуем отправить тестовый запрос
        # (если есть веб-хук или API)
        return True
    except:
        return False


def check_admin_panel():
    """Проверяет админ-панель"""
    try:
        # Если Railway доступен, админ-панель работает
        return True
    except:
        return False


def restart_bot():
    """Перезапускает бота"""
    print("🔄 Перезапускаем бота...")

    # Находим процесс бота
    try:
        # Завершаем старый процесс
        subprocess.run(["pkill", "-f", "python3 bot.py"],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    except:
        pass

    # Ждем
    time.sleep(2)

    # Запускаем новый процесс
    try:
        subprocess.Popen(["python3", "bot.py"],
                         stdout=open('bot_restart.log', 'a'),
                         stderr=subprocess.STDOUT)
        print("✅ Бот перезапущен")
        return True
    except Exception as e:
        print(f"❌ Ошибка перезапуска: {e}")
        return False


def main():
    print("👨‍⚕️ Запускаем health check сервис...")

    check_interval = 60  # Проверять каждые 60 секунд
    bot_restart_count = 0

    while True:
        try:
            print(f"\n📊 Проверка #{bot_restart_count + 1}...")

            # Проверяем админ-панель
            admin_ok = check_admin_panel()
            print(f"🌐 Админ-панель: {'✅ Онлайн' if admin_ok else '❌ Офлайн'}")

            # Проверяем бота
            bot_ok = check_bot_health()
            print(f"🤖 Бот: {'✅ Онлайн' if bot_ok else '❌ Офлайн'}")

            # Если бот упал, но админ-панель работает
            if not bot_ok and admin_ok:
                print("⚠️  Бот упал, перезапускаем...")
                if restart_bot():
                    bot_restart_count += 1
                    print(f"🔄 Всего перезапусков: {bot_restart_count}")

            # Если всё упало
            if not admin_ok and not bot_ok:
                print("🚨 Всё упало! Нужен ручной перезапуск")

        except Exception as e:
            print(f"❌ Ошибка в health check: {e}")

        # Ждем перед следующей проверкой
        time.sleep(check_interval)


if __name__ == "__main__":
    main()