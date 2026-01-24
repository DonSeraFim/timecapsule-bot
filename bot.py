import telebot
import sqlite3
import datetime
import os
import time
from threading import Thread

# Токен бота (Railway возьмет из переменных окружения)
TOKEN = os.environ.get('BOT_TOKEN', 'ВАШ_ТОКЕН_ЗДЕСЬ')

bot = telebot.TeleBot(TOKEN)

# Пути для Railway
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

print(f"🤖 Бот запущен на Railway!")
print(f"📁 Папка: {BASE_DIR}")
print(f"🗄️  База: {DB_PATH}")

# Словарь для временных данных
user_data = {}


# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome = """🕰️ *Time Capsule Bot*

Отправляй сообщения в будущее!
Можно отправить себе или другу.

*Команды:*
/new - Создать капсулу
/my - Мои капсулы
/help - Помощь

Нажми /new чтобы начать!"""
    bot.send_message(message.chat.id, welcome, parse_mode="Markdown")


# Команда /help
@bot.message_handler(commands=['help'])
def help_cmd(message):
    help_text = """❓ *Как пользоваться:*

1. /new - создать капсулу
2. Выбери "Себе" или "Другу"
3. Если другу - введи его ID
4. Отправь сообщение (текст/фото/голос)
5. Укажи дату (ДД.ММ.ГГГГ)

*Пример:* /new → Себе → "Привет!" → 25.12.2024"""
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")


# Команда /new
@bot.message_handler(commands=['new'])
def new_capsule(message):
    user_id = message.from_user.id
    user_data[user_id] = {'step': 'choose_receiver'}

    # Кнопки выбора
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add('👤 Себе', '👥 Другу')

    bot.send_message(message.chat.id, "👤 *Кому отправить капсулу?*",
                     reply_markup=markup, parse_mode="Markdown")


# Выбор получателя
@bot.message_handler(func=lambda m: m.text in ['👤 Себе', '👥 Другу'])
def choose_receiver(message):
    user_id = message.from_user.id
    markup = telebot.types.ReplyKeyboardRemove()

    if message.text == '👤 Себе':
        user_data[user_id]['receiver'] = 'self'
        bot.send_message(message.chat.id, "📨 *Отправь сообщение:*\nТекст, фото или голосовое",
                         reply_markup=markup, parse_mode="Markdown")
        user_data[user_id]['step'] = 'wait_content'
    else:
        user_data[user_id]['receiver'] = 'friend'
        bot.send_message(message.chat.id, "👥 *Введи ID друга:*\n(только цифры)",
                         reply_markup=markup, parse_mode="Markdown")
        user_data[user_id]['step'] = 'wait_id'


# Получение ID друга
@bot.message_handler(func=lambda m: user_data.get(m.from_user.id, {}).get('step') == 'wait_id')
def get_friend_id(message):
    user_id = message.from_user.id
    try:
        friend_id = int(message.text.strip())
        user_data[user_id]['friend_id'] = friend_id
        bot.send_message(message.chat.id, "📨 *Отправь сообщение:*")
        user_data[user_id]['step'] = 'wait_content'
    except:
        bot.send_message(message.chat.id, "❌ Только цифры! Попробуй снова:")


# Получение контента
@bot.message_handler(content_types=['text', 'photo', 'voice', 'video'])
def get_content(message):
    user_id = message.from_user.id

    if user_id not in user_data:
        return

    if user_data[user_id]['step'] == 'wait_content':
        # Сохраняем данные
        user_data[user_id]['type'] = message.content_type
        user_data[user_id]['text'] = message.text or message.caption or ""

        # Если есть файл
        if message.content_type in ['photo', 'voice', 'video']:
            if message.content_type == 'photo':
                file_id = message.photo[-1].file_id
            elif message.content_type == 'voice':
                file_id = message.voice.file_id
            else:
                file_id = message.video.file_id

            user_data[user_id]['file_id'] = file_id

            # Сохраняем файл
            try:
                file_info = bot.get_file(file_id)
                file_bytes = bot.download_file(file_info.file_path)

                ext = file_info.file_path.split('.')[-1]
                filename = f"{user_id}_{int(time.time())}.{ext}"
                filepath = os.path.join(MEDIA_PATH, filename)

                with open(filepath, 'wb') as f:
                    f.write(file_bytes)

                user_data[user_id]['file_path'] = filepath
            except:
                pass

        # Спрашиваем дату
        user_data[user_id]['step'] = 'wait_date'
        bot.send_message(message.chat.id, "📅 *Укажи дату доставки:*\nФормат: ДД.ММ.ГГГГ\nПример: 25.12.2024",
                         parse_mode="Markdown")


# Получение даты и сохранение
@bot.message_handler(func=lambda m: user_data.get(m.from_user.id, {}).get('step') == 'wait_date')
def get_date(message):
    user_id = message.from_user.id

    try:
        day, month, year = map(int, message.text.split('.'))
        send_date = datetime.datetime(year, month, day)

        # Проверяем что дата в будущем
        if send_date <= datetime.datetime.now():
            bot.send_message(message.chat.id, "❌ Дата должна быть в будущем!")
            return

        # Определяем получателя
        if user_data[user_id]['receiver'] == 'self':
            receiver_id = user_id
        else:
            receiver_id = user_data[user_id]['friend_id']

        # Сохраняем в базу
        cursor.execute('''
        INSERT INTO capsules 
        (sender_id, receiver_id, message_type, message_text, file_id, file_path, send_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            receiver_id,
            user_data[user_id]['type'],
            user_data[user_id]['text'],
            user_data[user_id].get('file_id', ''),
            user_data[user_id].get('file_path', ''),
            send_date.strftime('%Y-%m-%d')
        ))
        conn.commit()

        # Отправляем подтверждение
        formatted_date = send_date.strftime('%d %B %Y')

        if user_data[user_id]['receiver'] == 'self':
            receiver_text = "себе"
        else:
            receiver_text = f"другу (ID: {receiver_id})"

        confirm = f"""✅ *Капсула создана!*

👤 Для: {receiver_text}
📅 Доставка: {formatted_date}
📝 Тип: {user_data[user_id]['type']}

Ожидай доставки! 🕰️"""

        bot.send_message(message.chat.id, confirm, parse_mode="Markdown")

        # Уведомляем друга
        if user_data[user_id]['receiver'] == 'friend':
            try:
                bot.send_message(receiver_id,
                                 f"🎁 *Тебе создали капсулу времени!*\nОна придет: {formatted_date}\nОжидай сюрприз!",
                                 parse_mode="Markdown")
            except:
                pass

        # Очищаем данные
        del user_data[user_id]

    except Exception as e:
        bot.send_message(message.chat.id, "❌ Неверный формат!\nИспользуй: ДД.ММ.ГГГГ\nПример: 25.12.2024")


# Команда /my
@bot.message_handler(commands=['my'])
def my_capsules(message):
    user_id = message.from_user.id

    cursor.execute('''
    SELECT id, receiver_id, message_type, message_text, send_date, is_sent
    FROM capsules WHERE sender_id = ? ORDER BY send_date
    ''', (user_id,))

    capsules = cursor.fetchall()

    if not capsules:
        bot.send_message(message.chat.id, "📭 У тебя пока нет капсул.\nСоздай первую: /new")
        return

    text = "📋 *Твои капсулы:*\n\n"

    for cap in capsules[:10]:
        cap_id, receiver_id, mtype, mtext, sdate, sent = cap

        if receiver_id == user_id:
            receiver = "👤 Себе"
        else:
            receiver = f"👥 Другу (ID: {receiver_id})"

        # Сокращаем текст
        if mtext and len(mtext) > 30:
            preview = mtext[:30] + "..."
        else:
            preview = mtext or "(без текста)"

        # Статус
        if sent:
            status = "✅ Доставлено"
        else:
            try:
                send_date = datetime.datetime.strptime(sdate, '%Y-%m-%d')
                days_left = (send_date - datetime.datetime.now()).days
                status = f"⏳ Через {days_left} дней"
            except:
                status = "⏳ Ожидает"

        text += f"🆔 #{cap_id} {receiver}\n"
        text += f"📅 {sdate}\n"
        text += f"📄 {preview}\n"
        text += f"{status}\n\n"

    bot.send_message(message.chat.id, text, parse_mode="Markdown")


# Функция отправки капсул
def send_capsules():
    while True:
        try:
            today = datetime.datetime.now().strftime('%Y-%m-%d')

            cursor.execute('''
            SELECT id, sender_id, receiver_id, message_type, message_text, file_id, file_path
            FROM capsules WHERE send_date = ? AND is_sent = 0
            ''', (today,))

            for cap in cursor.fetchall():
                cap_id, sender_id, receiver_id, mtype, mtext, file_id, file_path = cap

                try:
                    # Отправляем сообщение
                    if mtype == 'text':
                        bot.send_message(receiver_id,
                                         f"🕰️ *Капсула времени доставлена!*\n\n{mtext}",
                                         parse_mode="Markdown")

                    elif mtype == 'photo':
                        if file_path and os.path.exists(file_path):
                            with open(file_path, 'rb') as f:
                                bot.send_photo(receiver_id, f,
                                               caption=f"🕰️ *Капсула времени доставлена!*\n\n{mtext}" if mtext else None)
                        elif file_id:
                            bot.send_photo(receiver_id, file_id,
                                           caption=f"🕰️ *Капсула времени доставлена!*\n\n{mtext}" if mtext else None)

                    elif mtype == 'voice':
                        if file_path and os.path.exists(file_path):
                            with open(file_path, 'rb') as f:
                                bot.send_voice(receiver_id, f,
                                               caption=f"🕰️ *Капсула времени доставлена!*\n\n{mtext}" if mtext else None)
                        elif file_id:
                            bot.send_voice(receiver_id, file_id,
                                           caption=f"🕰️ *Капсула времени доставлена!*\n\n{mtext}" if mtext else None)

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
            print(f"❌ Ошибка в send_capsules: {e}")

        time.sleep(60)  # Проверяем каждую минуту


# Запуск планировщика
def start_scheduler():
    thread = Thread(target=send_capsules, daemon=True)
    thread.start()


# Запуск бота
if __name__ == "__main__":
    print("🚀 Запускаем бота...")
    start_scheduler()
    print("✅ Бот запущен и слушает сообщения")
    bot.polling(none_stop=True)