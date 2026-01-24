"""
🎬 Video Capsule Admin Panel
Стильный интерфейс с просмотром кружков
"""

from flask import Flask, render_template, request, jsonify, send_file, Response
import sqlite3
import os
from datetime import datetime
import mimetypes
from pathlib import Path

app = Flask(__name__)

# Пароль для доступа
ADMIN_PASSWORD = "capsule2024"

# Пути
BASE_DIR = os.getcwd()
DB_PATH = os.path.join(BASE_DIR, 'capsules.db')
MEDIA_PATH = os.path.join(BASE_DIR, 'media')

print("=" * 60)
print("🎬 VIDEO CAPSULE ADMIN PANEL")
print("=" * 60)
print(f"📁 База данных: {DB_PATH}")
print(f"🎥 Папка медиа: {MEDIA_PATH}")
print(f"🔐 Пароль: {ADMIN_PASSWORD}")
print("=" * 60)


# Подключение к базе
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# Форматирование размера файла
def format_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


# Получение иконки по типу
def get_type_icon(msg_type):
    icons = {
        'text': '📝',
        'photo': '📸',
        'video': '🎥',
        'video_note': '🔄',
        'voice': '🎤'
    }
    return icons.get(msg_type, '📄')


# Получение типа на русском
def get_type_name(msg_type):
    names = {
        'text': 'Текст',
        'photo': 'Фото',
        'video': 'Видео',
        'video_note': 'Кружок',
        'voice': 'Голосовое'
    }
    return names.get(msg_type, msg_type)


# Главная страница
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        password = request.form.get('password')
        if password != ADMIN_PASSWORD:
            return render_template('login.html', error="Неверный пароль!")
        return render_template('dashboard.html')

    # Проверяем куки
    if request.cookies.get('admin_auth') == ADMIN_PASSWORD:
        return render_template('dashboard.html')

    return render_template('login.html')


# API для получения данных
@app.route('/api/capsules')
def api_capsules():
    conn = get_db()
    cursor = conn.cursor()

    # Получаем капсулы
    cursor.execute('''
    SELECT id, sender_id, receiver_id, message_type, message_text, 
           file_path, send_date, created_at, is_sent
    FROM capsules 
    ORDER BY created_at DESC 
    LIMIT 100
    ''')

    capsules = []
    for row in cursor.fetchall():
        cap = dict(row)

        # Добавляем иконку и название типа
        cap['icon'] = get_type_icon(cap['message_type'])
        cap['type_name'] = get_type_name(cap['message_type'])

        # Информация о файле
        if cap['file_path'] and os.path.exists(cap['file_path']):
            cap['has_file'] = True
            cap['file_name'] = os.path.basename(cap['file_path'])
            cap['file_size'] = format_size(os.path.getsize(cap['file_path']))

            # Определяем MIME-тип для превью
            mime_type, _ = mimetypes.guess_type(cap['file_path'])
            cap['mime_type'] = mime_type or 'application/octet-stream'

            # Для кружков специальная обработка
            if cap['message_type'] == 'video_note':
                cap['is_video_note'] = True
        else:
            cap['has_file'] = False

        # Дней до/после отправки
        try:
            send_date = datetime.strptime(cap['send_date'], '%Y-%m-%d')
            days_diff = (send_date - datetime.now()).days
            if cap['is_sent']:
                cap['status'] = 'delivered'
                cap['status_text'] = 'Доставлено'
            elif days_diff < 0:
                cap['status'] = 'overdue'
                cap['status_text'] = 'Просрочено'
            elif days_diff == 0:
                cap['status'] = 'today'
                cap['status_text'] = 'Сегодня'
            elif days_diff == 1:
                cap['status'] = 'tomorrow'
                cap['status_text'] = 'Завтра'
            else:
                cap['status'] = 'pending'
                cap['status_text'] = f'Через {days_diff} дн.'
        except:
            cap['status'] = 'unknown'
            cap['status_text'] = 'Неизвестно'

        capsules.append(cap)

    conn.close()
    return jsonify({'capsules': capsules})


# API для статистики
@app.route('/api/stats')
def api_stats():
    conn = get_db()
    cursor = conn.cursor()

    # Базовая статистика
    cursor.execute('SELECT COUNT(*) as total FROM capsules')
    total = cursor.fetchone()['total']

    cursor.execute('SELECT COUNT(*) as sent FROM capsules WHERE is_sent = 1')
    sent = cursor.fetchone()['sent']

    cursor.execute('SELECT COUNT(*) as with_files FROM capsules WHERE file_path IS NOT NULL AND file_path != ""')
    with_files = cursor.fetchone()['with_files']

    cursor.execute('SELECT COUNT(DISTINCT sender_id) as users FROM capsules')
    users = cursor.fetchone()['users']

    # Статистика по типам
    cursor.execute('''
    SELECT message_type, COUNT(*) as count 
    FROM capsules 
    GROUP BY message_type 
    ORDER BY count DESC
    ''')
    types_stats = cursor.fetchall()

    # Размер файлов
    cursor.execute('SELECT file_path FROM capsules WHERE file_path IS NOT NULL AND file_path != ""')
    files = cursor.fetchall()

    total_size = 0
    for file in files:
        try:
            if os.path.exists(file['file_path']):
                total_size += os.path.getsize(file['file_path'])
        except:
            pass

    # Последние 7 дней
    cursor.execute('''
    SELECT DATE(created_at) as date, COUNT(*) as count 
    FROM capsules 
    WHERE created_at >= DATE('now', '-7 days') 
    GROUP BY DATE(created_at) 
    ORDER BY date
    ''')
    last_7_days = cursor.fetchall()

    conn.close()

    stats = {
        'total': total,
        'sent': sent,
        'pending': total - sent,
        'with_files': with_files,
        'users': users,
        'total_size': format_size(total_size),
        'types': [dict(row) for row in types_stats],
        'last_7_days': [dict(row) for row in last_7_days],
        'sent_percent': round((sent / total * 100) if total > 0 else 0, 1)
    }

    return jsonify(stats)


# Просмотр файла
@app.route('/api/file/<int:capsule_id>')
def view_file(capsule_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT file_path, message_type FROM capsules WHERE id = ?', (capsule_id,))
    result = cursor.fetchone()
    conn.close()

    if not result or not result['file_path'] or not os.path.exists(result['file_path']):
        return jsonify({'error': 'File not found'}), 404

    file_path = result['file_path']

    # Для кружков - возвращаем как видео
    if result['message_type'] == 'video_note':
        mime_type = 'video/mp4'
    else:
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = 'application/octet-stream'

    return send_file(file_path, mimetype=mime_type)


# Скачивание файла
@app.route('/api/download/<int:capsule_id>')
def download_file(capsule_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT file_path FROM capsules WHERE id = ?', (capsule_id,))
    result = cursor.fetchone()
    conn.close()

    if not result or not result['file_path'] or not os.path.exists(result['file_path']):
        return jsonify({'error': 'File not found'}), 404

    file_path = result['file_path']
    file_name = os.path.basename(file_path)

    return send_file(file_path, as_attachment=True, download_name=file_name)


# Удаление файла
@app.route('/api/delete_file/<int:capsule_id>', methods=['POST'])
def delete_file(capsule_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT file_path FROM capsules WHERE id = ?', (capsule_id,))
    result = cursor.fetchone()

    if not result or not result['file_path']:
        conn.close()
        return jsonify({'success': False, 'error': 'Файл не найден'})

    file_path = result['file_path']

    try:
        # Удаляем файл с диска
        if os.path.exists(file_path):
            os.remove(file_path)

        # Очищаем путь в базе
        cursor.execute('UPDATE capsules SET file_path = NULL WHERE id = ?', (capsule_id,))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Файл удален'})

    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)})


# Аутентификация
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    password = data.get('password', '')

    if password == ADMIN_PASSWORD:
        response = jsonify({'success': True})
        response.set_cookie('admin_auth', ADMIN_PASSWORD, max_age=60 * 60 * 24 * 30)  # 30 дней
        return response
    else:
        return jsonify({'success': False, 'error': 'Неверный пароль'})


# Выход
@app.route('/api/logout')
def logout():
    response = jsonify({'success': True})
    response.set_cookie('admin_auth', '', expires=0)
    return response


# Шаблоны HTML
@app.route('/login.html')
def login_page():
    return render_template('login.html')


@app.route('/dashboard.html')
def dashboard_page():
    return render_template('dashboard.html')


# Статические файлы
@app.route('/assets/<path:filename>')
def static_files(filename):
    return send_file(f'assets/{filename}')


# Создаем папки для шаблонов и статики
os.makedirs('templates', exist_ok=True)
os.makedirs('assets', exist_ok=True)

# Запуск
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Админ-панель доступна на порту: {port}")
    print("🚀 Запуск...")
    app.run(host='0.0.0.0', port=port, debug=False)