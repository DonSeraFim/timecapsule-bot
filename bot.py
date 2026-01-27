import telebot
import sqlite3
import datetime
import os
import time
from threading import Thread
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = os.environ.get('BOT_TOKEN', '8262276813:AAG2SxWcGkai-Zxqo8AOvC13IQcZmRV65DQ')

bot = telebot.TeleBot(TOKEN)

# Пути
BASE_DIR = os.getcwd()
DB_PATH = os.path.join(BASE_DIR, 'capsules.db')
MEDIA_PATH = os.path.join(BASE_DIR, 'media')

# Создаем папку для медиа
if not os.path.exists(MEDIA_PATH):
    os.makedirs(MEDIA_PATH)

# Создаем базу данных
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS capsules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER,
    receiver_id INTEGER,
    message_type TEXT,
    message_text TEXT,
    file_id TEXT,
    file_path TEXT,
    send_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    is_sent INTEGER DEFAULT 0
)
''')
conn.commit()

print("=" * 50)
print("🎬 Time Capsule Bot запущен!")
print(f"📁 Папка: {BASE_DIR}")
print("📸 Поддерживает: текст, фото, видео, голосовые, кружки")
print("=" * 50)

# Хранилище состояний пользователей
user_states = {}


# ========== КОМАНДЫ ==========

@bot.message_handler(commands=['start'])
def start_command(message):
    """Обработчик команды /start"""
    text = """🎬 *Video Capsule Bot*

📹 Отправляй видео, фото, голосовые и КРУЖКИ в будущее!
Можно отправить себе или другу.

✨ *Что можно отправить:*
• 📸 Фото
• 🎥 Видео
• 🔄 Кружки (круговые видео)
• 🎤 Голосовые
• 📝 Текст

*Команды:*
/new - Создать капсулу
/my - Мои капсулы
/help - Помощь

Нажми /new чтобы начать!"""

    bot.send_message(message.chat.id, text, parse_mode="Markdown")
    print(f"👤 {message.from_user.id} использовал /start")


@bot.message_handler(commands=['help'])
def help_command(message):
    """Обработчик команды /help"""
    text = """❓ *Как пользоваться ботом:*

1. Нажми /new
2. Выбери "Себе" или "Другу"
3. Если "Другу" - введи его ID (цифры)
4. Отправь контент (фото, видео, кружок, голос, текст)
5. Укажи дату в формате *ДД.ММ.ГГГГ*

*Пример даты:* 25.12.2024

📌 *Что такое кружки?*
Это короткие круговые видео из Telegram (видеосообщения)

Чтобы узнать ID друга, отправь его к боту @userinfobot"""

    bot.send_message(message.chat.id, text, parse_mode="Markdown")
    print(f"👤 {message.from_user.id} использовал /help")


@bot.message_handler(commands=['my'])
def my_command(message):
    """Обработчик команды /my"""
    user_id = message.from_user.id
    print(f"👤 {user_id} запросил свои капсулы")

    # Получаем капсулы пользователя
    cursor.execute('''
    SELECT id, receiver_id, message_type, message_text, send_date, is_sent
    FROM capsules 
    WHERE sender_id = ? 
    ORDER BY created_at DESC 
    LIMIT 10
    ''', (user_id,))

    capsules = cursor.fetchall()

    if not capsules:
        bot.send_message(message.chat.id,
                         "📭 У тебя пока нет созданных капсул.\n"
                         "Создай первую: /new",
                         parse_mode="Markdown")
        return

    # Формируем ответ
    response = "🎬 *Твои капсулы:*\n\n"

    for cap in capsules:
        cap_id, receiver_id, msg_type, msg_text, send_date, is_sent = cap

        # Определяем получателя
        if receiver_id == user_id:
            receiver = "👤 Себе"
        else:
            receiver = f"👥 Другу (ID: {receiver_id})"

        # Сокращаем текст
        preview = ""
        if msg_text:
            if len(msg_text) > 30:
                preview = msg_text[:30] + "..."
            else:
                preview = msg_text
        else:
            preview = "(без текста)"

        # Иконка и тип
        if msg_type == 'text':
            icon = '📝'
            type_text = 'Текст'
        elif msg_type == 'photo':
            icon = '📸'
            type_text = 'Фото'
        elif msg_type == 'video':
            icon = '🎥'
            type_text = 'Видео'
        elif msg_type == 'video_note':
            icon = '🔄'
            type_text = 'Кружок'
        elif msg_type == 'voice':
            icon = '🎤'
            type_text = 'Голос'
        else:
            icon = '📄'
            type_text = msg_type

        # Статус
        if is_sent:
            status = "✅ Доставлено"
        else:
            try:
                send_date_obj = datetime.datetime.strptime(send_date, '%Y-%m-%d')
                days_left = (send_date_obj - datetime.datetime.now()).days
                if days_left <= 0:
                    status = "⏰ Ожидает отправки"
                elif days_left == 1:
                    status = "⏳ Завтра"
                else:
                    status = f"⏳ Через {days_left} дней"
            except:
                status = "⏳ В ожидании"

        response += f"{icon} *Капсула #{cap_id}*\n"
        response += f"   👤 {receiver}\n"
        response += f"   📅 {send_date} | {type_text}\n"
        response += f"   {status}\n\n"

    response += "Создать новую: /new"

    bot.send_message(message.chat.id, response, parse_mode="Markdown")
    print(f"📊 Показано {len(capsules)} капсул для {user_id}")


@bot.message_handler(commands=['new'])
def new_command(message):
    """Обработчик команды /new"""
    user_id = message.from_user.id

    # Сбрасываем старое состояние
    if user_id in user_states:
        del user_states[user_id]

    # Создаем новое состояние
    user_states[user_id] = {
        'step': 'ask_receiver',
        'created_at': datetime.datetime.now()
    }

    # Создаем кнопки
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add('👤 Себе', '👥 Другу')

    bot.send_message(message.chat.id,
                     "👤 *Кому отправить капсулу?*\n\n"
                     "Выбери вариант:",
                     reply_markup=markup,
                     parse_mode="Markdown")

    print(f"🆕 {user_id} начал создание капсулы")


# ========== ОБРАБОТКА СООБЩЕНИЙ ==========

@bot.message_handler(func=lambda m: m.text in ['👤 Себе', '👥 Другу'])
def handle_receiver(message):
    """Обработка выбора получателя"""
    user_id = message.from_user.id

    if user_id not in user_states:
        bot.send_message(message.chat.id, "❌ Начни заново: /new")
        return

    if user_states[user_id]['step'] != 'ask_receiver':
        return

    # Убираем клавиатуру
    markup = telebot.types.ReplyKeyboardRemove()

    if message.text == '👤 Себе':
        user_states[user_id]['receiver'] = 'self'
        user_states[user_id]['receiver_id'] = user_id
        user_states[user_id]['step'] = 'ask_content'

        bot.send_message(message.chat.id,
                         "🎬 *Отправь контент для капсулы:*\n\n"
                         "Можно отправить:\n"
                         "• 📸 Фото\n"
                         "• 🎥 Видео\n"
                         "• 🔄 Кружок\n"
                         "• 🎤 Голосовое\n"
                         "• 📝 Текст",
                         reply_markup=markup,
                         parse_mode="Markdown")

    elif message.text == '👥 Другу':
        user_states[user_id]['receiver'] = 'friend'
        user_states[user_id]['step'] = 'ask_friend_id'

        bot.send_message(message.chat.id,
                         "👥 *Введи ID друга:*\n\n"
                         "ID должен содержать только цифры.\n"
                         "Пример: 123456789\n\n"
                         "Чтобы узнать ID, отправь друга к боту @userinfobot",
                         reply_markup=markup,
                         parse_mode="Markdown")

    print(f"👤 {user_id} выбрал: {message.text}")


@bot.message_handler(func=lambda m: user_states.get(m.from_user.id, {}).get('step') == 'ask_friend_id')
def handle_friend_id(message):
    """Обработка ID друга"""
    user_id = message.from_user.id

    try:
        friend_id = int(message.text.strip())
        user_states[user_id]['receiver_id'] = friend_id
        user_states[user_id]['step'] = 'ask_content'

        bot.send_message(message.chat.id,
                         f"✅ ID друга принят: {friend_id}\n\n"
                         "🎬 *Теперь отправь контент для капсулы:*\n\n"
                         "Можно отправить:\n"
                         "• 📸 Фото\n"
                         "• 🎥 Видео\n"
                         "• 🔄 Кружок\n"
                         "• 🎤 Голосовое\n"
                         "• 📝 Текст",
                         parse_mode="Markdown")

        print(f"👥 {user_id} ввел ID друга: {friend_id}")

    except ValueError:
        bot.send_message(message.chat.id,
                         "❌ Неверный формат!\n\n"
                         "ID должен содержать только цифры.\n"
                         "Пример: 123456789\n\n"
                         "Попробуй снова:")


@bot.message_handler(content_types=['text', 'photo', 'video', 'video_note', 'voice'],
                     func=lambda m: user_states.get(m.from_user.id, {}).get('step') == 'ask_content')
def handle_content(message):
    """Обработка содержимого капсулы"""
    user_id = message.from_user.id

    # Определяем тип сообщения
    if message.content_type == 'video_note':
        msg_type = 'video_note'
        type_text = 'Кружок'
    else:
        msg_type = message.content_type

    # Сохраняем данные
    user_states[user_id]['message_type'] = msg_type
    user_states[user_id]['message_text'] = message.text or message.caption or ""

    # Обрабатываем файлы
    if message.content_type in ['photo', 'video', 'video_note', 'voice']:
        try:
            if message.content_type == 'photo':
                file_id = message.photo[-1].file_id
                ext = 'jpg'
            elif message.content_type == 'video':
                file_id = message.video.file_id
                ext = 'mp4'
            elif message.content_type == 'video_note':  # Кружки
                file_id = message.video_note.file_id
                ext = 'mp4'
                type_text = 'Кружок'
            elif message.content_type == 'voice':
                file_id = message.voice.file_id
                ext = 'ogg'

            user_states[user_id]['file_id'] = file_id

            # Скачиваем файл
            file_info = bot.get_file(file_id)
            downloaded = bot.download_file(file_info.file_path)

            # Сохраняем
            filename = f"{user_id}_{int(time.time())}.{ext}"
            filepath = os.path.join(MEDIA_PATH, filename)

            with open(filepath, 'wb') as f:
                f.write(downloaded)

            user_states[user_id]['file_path'] = filepath
            print(f"💾 Файл сохранен: {filepath}")

        except Exception as e:
            print(f"⚠️ Ошибка сохранения файла: {e}")

    # Переходим к следующему шагу
    user_states[user_id]['step'] = 'ask_date'

    # Определяем получателя для текста
    if user_states[user_id]['receiver'] == 'self':
        receiver_text = "себе"
    else:
        receiver_text = f"другу (ID: {user_states[user_id]['receiver_id']})"

    # Текст в зависимости от типа
    type_icon = ''
    if msg_type == 'photo':
        type_icon = '📸'
    elif msg_type == 'video':
        type_icon = '🎥'
    elif msg_type == 'video_note':
        type_icon = '🔄'
    elif msg_type == 'voice':
        type_icon = '🎤'
    else:
        type_icon = '📝'

    bot.send_message(message.chat.id,
                     f"✅ {type_icon} Контент принят!\n\n"
                     f"📅 *Теперь укажи дату, когда {receiver_text} получит сообщение*\n\n"
                     "*Формат:* ДД.ММ.ГГГГ\n"
                     "*Пример:* 25.12.2024\n\n"
                     "Можно указать любую дату в будущем!",
                     parse_mode="Markdown")

    print(f"📝 {user_id} отправил контент типа: {msg_type}")


@bot.message_handler(func=lambda m: user_states.get(m.from_user.id, {}).get('step') == 'ask_date')
def handle_date(message):
    """Обработка даты доставки"""
    user_id = message.from_user.id

    try:
        # Парсим дату
        parts = message.text.split('.')
        if len(parts) != 3:
            raise ValueError

        day, month, year = map(int, parts)
        send_date = datetime.datetime(year, month, day)

        # Проверяем что дата в будущем
        if send_date <= datetime.datetime.now():
            bot.send_message(message.chat.id, "❌ Дата должна быть в будущем! Попробуй снова:")
            return

        # Получаем данные из состояния
        receiver_id = user_states[user_id]['receiver_id']
        msg_type = user_states[user_id]['message_type']
        msg_text = user_states[user_id]['message_text']
        file_id = user_states[user_id].get('file_id', '')
        file_path = user_states[user_id].get('file_path', '')

        # Сохраняем в базу
        cursor.execute('''
        INSERT INTO capsules 
        (sender_id, receiver_id, message_type, message_text, file_id, file_path, send_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            receiver_id,
            msg_type,
            msg_text,
            file_id,
            file_path,
            send_date.strftime('%Y-%m-%d')
        ))
        conn.commit()

        # Получаем ID капсулы
        capsule_id = cursor.lastrowid

        # Форматируем дату
        formatted_date = send_date.strftime('%d %B %Y')

        # Определяем текст получателя
        if user_states[user_id]['receiver'] == 'self':
            receiver_text = "себе"
        else:
            receiver_text = f"другу (ID: {receiver_id})"

        # Иконка в зависимости от типа
        if msg_type == 'photo':
            icon = '📸'
        elif msg_type == 'video':
            icon = '🎥'
        elif msg_type == 'video_note':
            icon = '🔄'
        elif msg_type == 'voice':
            icon = '🎤'
        else:
            icon = '📝'

        # Отправляем подтверждение
        confirm = f"""✅ *Капсула создана!*

{icon} *Тип:* {'Кружок' if msg_type == 'video_note' else msg_type}
👤 *Для:* {receiver_text}
📅 *Доставка:* {formatted_date}
🆔 *Номер:* #{capsule_id}

Капсула будет отправлена автоматически в указанный день.

Создать ещё: /new
Мои капсулы: /my"""

        bot.send_message(message.chat.id, confirm, parse_mode="Markdown")

        # Уведомляем друга
        if user_states[user_id]['receiver'] == 'friend':
            try:
                bot.send_message(receiver_id,
                                 f"🎁 *Тебе создали капсулу времени!*\n\n"
                                 f"Она придет: {formatted_date}\n"
                                 f"Ожидай сюрприз! 🎉",
                                 parse_mode="Markdown")
            except Exception as e:
                print(f"⚠️ Не удалось уведомить друга {receiver_id}: {e}")

        print(f"✅ Создана капсула #{capsule_id}: {user_id} → {receiver_id} на {formatted_date}")

        # Очищаем состояние
        del user_states[user_id]

    except ValueError:
        bot.send_message(message.chat.id,
                         "❌ Неверный формат даты!\n\n"
                         "*Правильный формат:* ДД.ММ.ГГГГ\n"
                         "*Пример:* 25.12.2024\n\n"
                         "Попробуй снова:")
    except Exception as e:
        print(f"❌ Ошибка при создании капсулы: {e}")
        bot.send_message(message.chat.id,
                         "❌ Произошла ошибка при создании капсулы.\n"
                         "Попробуй снова: /new")
        if user_id in user_states:
            del user_states[user_id]


# ========== ФУНКЦИЯ ОТПРАВКИ КАПСУЛ ==========

def send_scheduled_capsules():
    """Функция для отправки капсул по расписанию"""
    while True:
        try:
            today = datetime.datetime.now().strftime('%Y-%m-%d')

            # Ищем капсулы на сегодня
            cursor.execute('''
            SELECT id, sender_id, receiver_id, message_type, message_text, file_id, file_path
            FROM capsules 
            WHERE send_date = ? AND is_sent = 0
            ''', (today,))

            capsules = cursor.fetchall()

            for cap in capsules:
                cap_id, sender_id, receiver_id, msg_type, msg_text, file_id, file_path = cap

                try:
                    # Отправляем в зависимости от типа
                    if msg_type == 'text':
                        bot.send_message(receiver_id,
                                         f"🎬 *Капсула времени доставлена!*\n\n{msg_text}",
                                         parse_mode="Markdown")

                    elif msg_type == 'photo':
                        if file_path and os.path.exists(file_path):
                            with open(file_path, 'rb') as f:
                                bot.send_photo(receiver_id, f,
                                               caption=f"🎬 *Капсула времени доставлена!*\n\n{msg_text}" if msg_text else None)
                        elif file_id:
                            bot.send_photo(receiver_id, file_id,
                                           caption=f"🎬 *Капсула времени доставлена!*\n\n{msg_text}" if msg_text else None)

                    elif msg_type == 'video':
                        if file_path and os.path.exists(file_path):
                            with open(file_path, 'rb') as f:
                                bot.send_video(receiver_id, f,
                                               caption=f"🎬 *Капсула времени доставлена!*\n\n{msg_text}" if msg_text else None)
                        elif file_id:
                            bot.send_video(receiver_id, file_id,
                                           caption=f"🎬 *Капсула времени доставлена!*\n\n{msg_text}" if msg_text else None)

                    elif msg_type == 'video_note':  # Кружки
                        if file_path and os.path.exists(file_path):
                            with open(file_path, 'rb') as f:
                                bot.send_video_note(receiver_id, f)
                        elif file_id:
                            bot.send_video_note(receiver_id, file_id)

                    elif msg_type == 'voice':
                        if file_path and os.path.exists(file_path):
                            with open(file_path, 'rb') as f:
                                bot.send_voice(receiver_id, f,
                                               caption=f"🎬 *Капсула времени доставлена!*\n\n{msg_text}" if msg_text else None)
                        elif file_id:
                            bot.send_voice(receiver_id, file_id,
                                           caption=f"🎬 *Капсула времени доставлена!*\n\n{msg_text}" if msg_text else None)

                    # Уведомляем отправителя
                    if sender_id != receiver_id:
                        try:
                            bot.send_message(sender_id, f"✅ Капсула #{cap_id} доставлена!")
                        except:
                            pass

                    # Помечаем как отправленную
                    cursor.execute('UPDATE capsules SET is_sent = 1 WHERE id = ?', (cap_id,))
                    conn.commit()

                    print(f"📨 Отправлена капсула #{cap_id}")

                except Exception as e:
                    print(f"❌ Ошибка отправки капсулы #{cap_id}: {e}")

        except Exception as e:
            print(f"❌ Ошибка в send_scheduled_capsules: {e}")

        time.sleep(60)  # Проверяем каждую минуту


# Запуск планировщика в отдельном потоке
def start_scheduler():
    """Запуск планировщика отправки капсул"""
    thread = Thread(target=send_scheduled_capsules, daemon=True)
    thread.start()
    print("⏰ Планировщик отправки капсул запущен")


# ========== ЗАПУСК БОТА ==========

# Запуск бота
if __name__ == "__main__":
    print("🚀 Запускаем Video Capsule Bot...")
    
    try:
        # Запускаем планировщик
        start_scheduler()
        
        print("✅ Бот запущен и готов к работе!")
        print("📞 Ожидаю сообщения...")
        
        # Запускаем бота с обработкой ошибок
        while True:
            try:
                bot.polling(none_stop=True, interval=1, timeout=20)
            except Exception as e:
                logger.error(f"❌ Ошибка в polling: {e}")
                print(f"❌ Бот упал: {e}")
                print("🔄 Перезапуск через 5 секунд...")
                time.sleep(5)
                
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        print(f"❌ Критическая ошибка: {e}")
