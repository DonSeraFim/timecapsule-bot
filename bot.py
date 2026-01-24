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
3. Если другу - введи его ID (цифры)
4. Отправь сообщение (текст/фото/голос)
5. Укажи дату в формате *ДД.ММ.ГГГГ*

*Пример:* 25.12.2024"""
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

# Команда /new
@bot.message_handler(commands=['new'])
def new_capsule(message):
    user_id = message.from_user.id
    user_data[user_id] = {'step': 'choose_receiver'}
    
    # Кнопки выбора
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add('👤 Себе', '👥 Другу')
    
    bot.send_message(message.chat.id, "👤 *Кому отправить капсулу?*\nВыбери вариант:", 
                     reply_markup=markup, parse_mode="Markdown")

# Выбор получателя
@bot.message_handler(func=lambda m: m.text in ['👤 Себе', '👥 Другу'])
def choose_receiver(message):
    user_id = message.from_user.id
    
    if user_id not in user_data:
        bot.send_message(message.chat.id, "❌ Начни заново: /new")
        return
    
    markup = telebot.types.ReplyKeyboardRemove()
    
    if message.text == '👤 Себе':
        user_data[user_id]['receiver'] = 'self'
        bot.send_message(message.chat.id, 
                        "📨 *Отправь сообщение для капсулы:*\n\nМожно отправить:\n• Текст\n• Фото (с подписью или без)\n• Голосовое сообщение\n• Видео",
                        reply_markup=markup, parse_mode="Markdown")
        user_data[user_id]['step'] = 'wait_content'
        
    elif message.text == '👥 Другу':
        user_data[user_id]['receiver'] = 'friend'
        bot.send_message(message.chat.id, 
                        "👥 *Введи ID друга:*\n(Только цифры)\n\nЧтобы узнать ID друга, отправь его к боту @userinfobot",
                        reply_markup=markup, parse_mode="Markdown")
        user_data[user_id]['step'] = 'wait_friend_id'

# Получение ID друга
@bot.message_handler(func=lambda m: user_data.get(m.from_user.id, {}).get('step') == 'wait_friend_id')
def get_friend_id(message):
    user_id = message.from_user.id
    
    try:
        friend_id = int(message.text.strip())
        user_data[user_id]['friend_id'] = friend_id
        
        bot.send_message(message.chat.id,
                        f"✅ ID друга принят: {friend_id}\n\n"
                        "📨 *Теперь отправь сообщение для капсулы:*\n\n"
                        "Можно отправить:\n• Текст\n• Фото (с подписью или без)\n• Голосовое сообщение\n• Видео",
                        parse_mode="Markdown")
        
        user_data[user_id]['step'] = 'wait_content'
        
    except ValueError:
        bot.send_message(message.chat.id,
                        "❌ Неверный формат ID!\n"
                        "ID должен содержать только цифры.\n"
                        "Пример: 123456789\n\n"
                        "Попробуй снова:")

# Получение контента (текст, фото, голос, видео)
@bot.message_handler(content_types=['text', 'photo', 'voice', 'video'])
def get_content(message):
    user_id = message.from_user.id
    
    if user_id not in user_data:
        return
    
    if user_data[user_id]['step'] != 'wait_content':
        return
    
    # Сохраняем тип сообщения и текст
    user_data[user_id]['type'] = message.content_type
    user_data[user_id]['text'] = message.text or message.caption or ""
    
    # Если есть файл (фото, голос, видео)
    if message.content_type in ['photo', 'voice', 'video']:
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
        elif message.content_type == 'voice':
            file_id = message.voice.file_id
        elif message.content_type == 'video':
            file_id = message.video.file_id
        
        user_data[user_id]['file_id'] = file_id
        
        # Пытаемся скачать и сохранить файл
        try:
            file_info = bot.get_file(file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            file_extension = file_info.file_path.split('.')[-1]
            filename = f"{user_id}_{int(time.time())}.{file_extension}"
            filepath = os.path.join(MEDIA_PATH, filename)
            
            with open(filepath, 'wb') as new_file:
                new_file.write(downloaded_file)
            
            user_data[user_id]['file_path'] = filepath
            print(f"✅ Файл сохранен: {filepath}")
        except Exception as e:
            print(f"⚠️ Не удалось сохранить файл: {e}")
    
    # Переходим к следующему шагу
    user_data[user_id]['step'] = 'wait_date'
    
    # Определяем получателя для текста
    if user_data[user_id]['receiver'] == 'self':
        receiver_text = "себе"
    else:
        receiver_text = f"другу (ID: {user_data[user_id]['friend_id']})"
    
    bot.send_message(message.chat.id,
                    f"📅 *Отлично! Теперь укажи дату, когда {receiver_text} получит сообщение*\n\n"
                    "*Формат:* ДД.ММ.ГГГГ\n"
                    "*Пример:* 25.12.2024\n\n"
                    "Можно указать любую дату в будущем!",
                    parse_mode="Markdown")

# Получение даты и сохранение капсулы
@bot.message_handler(func=lambda m: user_data.get(m.from_user.id, {}).get('step') == 'wait_date')
def get_date(message):
    user_id = message.from_user.id
    
    # Проверяем, что пользователь в процессе создания капсулы
    if user_id not in user_data:
        bot.send_message(message.chat.id, "❌ Что-то пошло не так. Начни заново: /new")
        return
    
    try:
        # Пытаемся разобрать дату
        day, month, year = map(int, message.text.split('.'))
        send_date = datetime.datetime(year, month, day)
        
        # Проверяем, что дата в будущем
        if send_date <= datetime.datetime.now():
            bot.send_message(message.chat.id, "❌ Дата должна быть в будущем! Попробуй снова:")
            return
        
        # Определяем ID получателя
        if user_data[user_id]['receiver'] == 'self':
            receiver_id = user_id
            receiver_text = "себе"
        else:
            receiver_id = user_data[user_id]['friend_id']
            receiver_text = f"другу (ID: {receiver_id})"
        
        # Сохраняем в базу данных
        cursor.execute('''
        INSERT INTO capsules 
        (sender_id, receiver_id, message_type, message_text, file_id, file_path, send_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,  # отправитель
            receiver_id,  # получатель
            user_data[user_id]['type'],
            user_data[user_id]['text'],
            user_data[user_id].get('file_id', ''),
            user_data[user_id].get('file_path', ''),
            send_date.strftime('%Y-%m-%d')
        ))
        conn.commit()
        
        # Получаем ID созданной капсулы
        capsule_id = cursor.lastrowid
        
        # Форматируем красивую дату для сообщения
        formatted_date = send_date.strftime('%d %B %Y')
        
        # Отправляем подтверждение создателю
        confirmation = f"""✅ *Капсула создана!*

🆔 Номер: #{capsule_id}
👤 Получатель: {receiver_text}
📅 Дата получения: {formatted_date}
📝 Тип: {user_data[user_id]['type']}
⏳ Ожидай доставки!

Капсула будет отправлена автоматически в указанный день.

Создать ещё капсулу: /new
Посмотреть свои капсулы: /my
"""
        bot.send_message(message.chat.id, confirmation, parse_mode="Markdown")
        
        # Если отправляем другу - уведомляем его
        if user_data[user_id]['receiver'] == 'friend':
            try:
                friend_notification = f"""🎁 *Тебе создали капсулу времени!*

Кто-то отправил тебе сообщение в будущее!
Оно придет: {formatted_date}

Ожидай сюрприз! 🎉"""
                bot.send_message(receiver_id, friend_notification, parse_mode="Markdown")
            except Exception as e:
                print(f"⚠️ Не удалось уведомить друга {receiver_id}: {e}")
                # Можно не сообщать отправителю об этой ошибке
        
        print(f"✅ Создана капсула #{capsule_id}: {user_id} → {receiver_id} на {formatted_date}")
        
        # Очищаем временные данные
        del user_data[user_id]
        
    except ValueError:
        # Если не удалось разобрать дату
        bot.send_message(message.chat.id, 
                        "❌ Неверный формат даты!\n\n"
                        "*Правильный формат:* ДД.ММ.ГГГГ\n"
                        "*Примеры:*\n"
                        "• 25.12.2024\n"
                        "• 01.01.2025\n"
                        "• 14.02.2024\n\n"
                        "Попробуй снова:")
    except Exception as e:
        print(f"❌ Ошибка при создании капсулы: {e}")
        bot.send_message(message.chat.id, 
                        "❌ Произошла ошибка при создании капсулы.\n"
                        "Попробуй снова: /new")
        # Очищаем данные в случае ошибки
        if user_id in user_data:
            del user_data[user_id]

# Команда /my
@bot.message_handler(commands=['my'])
def my_capsules(message):
    user_id = message.from_user.id
    
    # Получаем капсулы, где пользователь - отправитель
    cursor.execute('''
    SELECT id, receiver_id, message_type, message_text, send_date, created_at, is_sent
    FROM capsules 
    WHERE sender_id = ?
    ORDER BY send_date
    LIMIT 20
    ''', (user_id,))
    
    capsules = cursor.fetchall()
    
    if not capsules:
        bot.send_message(message.chat.id, 
                        "📭 У тебя пока нет созданных капсул.\n"
                        "Создай первую: /new")
        return
    
    response = "📋 *Твои капсулы времени:*\n\n"
    
    for capsule in capsules:
        capsule_id, receiver_id, msg_type, msg_text, send_date, created_at, is_sent = capsule
        
        # Определяем получателя
        if receiver_id == user_id:
            receiver = "👤 Себе"
        else:
            receiver = f"👥 Другу (ID: {receiver_id})"
        
        # Сокращаем длинный текст
        if msg_text and len(msg_text) > 30:
            preview = msg_text[:30] + "..."
        else:
            preview = msg_text or "(без текста)"
        
        # Определяем статус
        if is_sent:
            status = "✅ Доставлено"
        else:
            try:
                send_date_obj = datetime.datetime.strptime(send_date, '%Y-%m-%d')
                now = datetime.datetime.now()
                if send_date_obj < now:
                    status = "⏰ Ожидает отправки"
                else:
                    days_left = (send_date_obj - now).days
                    if days_left == 0:
                        status = "⏳ Сегодня"
                    elif days_left == 1:
                        status = "⏳ Завтра"
                    else:
                        status = f"⏳ Через {days_left} дней"
            except:
                status = "⏳ В ожидании"
        
        # Иконка в зависимости от типа
        icons = {
            'text': '📝',
            'photo': '📸',
            'voice': '🎤',
            'video': '🎥'
        }
        icon = icons.get(msg_type, '📄')
        
        # Форматируем дату
        try:
            nice_date = datetime.datetime.strptime(send_date, '%Y-%m-%d').strftime('%d.%m.%Y')
        except:
            nice_date = send_date
        
        response += f"{icon} *Капсула #{capsule_id}*\n"
        response += f"👤 {receiver}\n"
        response += f"📅 {nice_date}\n"
        response += f"📄 {preview}\n"
        response += f"{status}\n\n"
    
    if len(capsules) == 20:
        response += "Показаны последние 20 капсул\n"
    
    response += "Создать новую капсулу: /new"
    
    bot.send_message(message.chat.id, response, parse_mode="Markdown")

# Функция для проверки и отправки капсул
def check_and_send_capsules():
    while True:
        try:
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            
            # Ищем капсулы на сегодня
            cursor.execute('''
            SELECT id, sender_id, receiver_id, message_type, message_text, file_id, file_path
            FROM capsules 
            WHERE send_date = ? AND is_sent = 0
            ''', (today,))
            
            capsules_to_send = cursor.fetchall()
            
            for capsule in capsules_to_send:
                capsule_id, sender_id, receiver_id, msg_type, msg_text, file_id, file_path = capsule
                
                try:
                    # Отправляем сообщение в зависимости от типа
                    if msg_type == 'text':
                        bot.send_message(receiver_id, 
                                       f"🕰️ *Капсула времени доставлена!*\n\n{msg_text}",
                                       parse_mode="Markdown")
                    
                    elif msg_type == 'photo':
                        if file_path and os.path.exists(file_path):
                            with open(file_path, 'rb') as photo:
                                bot.send_photo(receiver_id, photo, 
                                             caption=f"🕰️ *Капсула времени доставлена!*\n\n{msg_text}" if msg_text else None)
                        elif file_id:
                            bot.send_photo(receiver_id, file_id,
                                         caption=f"🕰️ *Капсула времени доставлена!*\n\n{msg_text}" if msg_text else None)
                    
                    elif msg_type == 'voice':
                        if file_path and os.path.exists(file_path):
                            with open(file_path, 'rb') as voice:
                                bot.send_voice(receiver_id, voice,
                                             caption=f"🕰️ *Капсула времени доставлена!*\n\n{msg_text}" if msg_text else None)
                        elif file_id:
                            bot.send_voice(receiver_id, file_id,
                                         caption=f"🕰️ *Капсула времени доставлена!*\n\n{msg_text}" if msg_text else None)
                    
                    # Уведомляем отправителя об успешной доставке (если не себе)
                    if sender_id != receiver_id:
                        try:
                            bot.send_message(sender_id,
                                           f"✅ Капсула #{capsule_id} успешно доставлена получателю!")
                        except:
                            pass
                    
                    # Помечаем как отправленную
                    cursor.execute('UPDATE capsules SET is_sent = 1 WHERE id = ?', (capsule_id,))
                    conn.commit()
                    
                    print(f"📨 Отправлена капсула #{capsule_id} от {sender_id} к {receiver_id}")
                    
                except Exception as e:
                    print(f"❌ Ошибка отправки капсулы #{capsule_id}: {e}")
                    
        except Exception as e:
            print(f"❌ Ошибка в check_and_send_capsules: {e}")
        
        # Ждем 60 секунд перед следующей проверкой
        time.sleep(60)

# Запускаем проверку капсул в отдельном потоке
def start_scheduler():
    scheduler_thread = Thread(target=check_and_send_capsules)
    scheduler_thread.daemon = True
    scheduler_thread.start()

# Обработчик для всех остальных сообщений (для отладки)
@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    user_id = message.from_user.id
    
    # Если пользователь в процессе создания капсулы, но что-то пошло не так
    if user_id in user_data:
        current_step = user_data[user_id].get('step')
        
        if current_step == 'wait_date':
            bot.send_message(message.chat.id,
                           "📅 Пожалуйста, укажи дату в формате *ДД.ММ.ГГГГ*\n"
                           "Пример: 25.12.2024\n\n"
                           "Если хочешь отменить создание капсулы, просто подожди 10 минут "
                           "или начни заново командой /new",
                           parse_mode="Markdown")
        elif current_step == 'wait_friend_id':
            bot.send_message(message.chat.id,
                           "👥 Пожалуйста, введи ID друга (только цифры)\n"
                           "Пример: 123456789\n\n"
                           "Чтобы узнать ID, отправь друга к боту @userinfobot")
        elif current_step == 'wait_content':
            bot.send_message(message.chat.id,
                           "📨 Пожалуйста, отправь сообщение для капсулы:\n"
                           "• Текст\n• Фото\n• Голосовое сообщение\n• Видео")
        else:
            bot.send_message(message.chat.id,
                           "Похоже, что-то пошло не так с созданием капсулы.\n"
                           "Начни заново: /new")
            # Очищаем данные
            if user_id in user_data:
                del user_data[user_id]
    else:
        # Если пользователь просто пишет текст без команд
        if message.text and not message.text.startswith('/'):
            bot.send_message(message.chat.id,
                           "👋 Привет! Я бот-капсула времени.\n\n"
                           "Используй команды:\n"
                           "• /start - начало работы\n"
                           "• /new - создать капсулу\n"
                           "• /my - мои капсулы\n"
                           "• /help - помощь\n\n"
                           "Выбери команду из меню или введи её вручную.")

# Запуск бота
if __name__ == "__main__":
    print("🚀 Запускаем Time Capsule Bot...")
    print("⏰ Запускаем планировщик отправки капсул...")
    
    # Запускаем планировщик
    start_scheduler()
    
    print("✅ Бот запущен и слушает сообщения")
    print("📞 Готов принимать команды...")
    
    # Запускаем бота
    bot.polling(none_stop=True, interval=2, timeout=30)
