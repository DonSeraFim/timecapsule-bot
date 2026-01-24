"""
📊 АДМИН-ПАНЕЛЬ для Time Capsule Bot на Railway
С возможностью просмотра файлов
"""

from flask import Flask, render_template_string, request, jsonify, send_file
import sqlite3
import os
from datetime import datetime
import mimetypes

app = Flask(__name__)

# Пароль для доступа (ИЗМЕНИ НА СВОЙ!)
ADMIN_PASSWORD = "donskov2011"

# Пути
BASE_DIR = os.getcwd()
DB_PATH = os.path.join(BASE_DIR, 'capsules.db')
MEDIA_PATH = os.path.join(BASE_DIR, 'media')

print(f"🔧 Админ-панель запущена!")
print(f"🗄️  База данных: {DB_PATH}")
print(f"🖼️  Папка медиа: {MEDIA_PATH}")

# HTML шаблон с просмотром файлов
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>🕰️ Time Capsule Admin</title>
    <meta charset="utf-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        header {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        h1 { 
            font-size: 2.5em; 
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s;
        }
        .stat-card:hover {
            transform: translateY(-5px);
        }
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            color: #4facfe;
            margin: 10px 0;
        }
        .stat-label {
            color: #666;
            font-size: 1.1em;
        }
        .tabs {
            display: flex;
            background: #f8f9fa;
            border-bottom: 2px solid #dee2e6;
        }
        .tab {
            padding: 15px 30px;
            background: none;
            border: none;
            font-size: 1.1em;
            cursor: pointer;
            transition: all 0.3s;
        }
        .tab:hover {
            background: #e9ecef;
        }
        .tab.active {
            background: white;
            border-bottom: 3px solid #4facfe;
            font-weight: bold;
        }
        .tab-content {
            padding: 30px;
        }
        .capsules-list, .files-list {
            display: none;
        }
        .content-active {
            display: block;
        }
        .capsule, .file-item {
            background: white;
            border-left: 5px solid #4facfe;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 8px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        }
        .capsule.delivered {
            border-left-color: #28a745;
            background: #f8fff9;
        }
        .capsule.pending {
            border-left-color: #ffc107;
            background: #fffdf6;
        }
        .capsule-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            flex-wrap: wrap;
            gap: 10px;
        }
        .capsule-id {
            font-weight: bold;
            color: #4facfe;
            font-size: 1.2em;
        }
        .capsule-users {
            display: flex;
            gap: 15px;
            margin: 10px 0;
            flex-wrap: wrap;
        }
        .user-badge {
            background: #e9ecef;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.9em;
        }
        .user-badge.sender {
            background: #d1ecf1;
            color: #0c5460;
        }
        .user-badge.receiver {
            background: #d4edda;
            color: #155724;
        }
        .capsule-text {
            margin: 15px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
            line-height: 1.6;
        }
        .capsule-meta {
            display: flex;
            gap: 15px;
            margin-top: 15px;
            flex-wrap: wrap;
        }
        .meta-item {
            background: #e9ecef;
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 0.9em;
        }
        .file-preview {
            margin: 15px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            text-align: center;
        }
        .file-image {
            max-width: 300px;
            max-height: 200px;
            border-radius: 5px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.2);
        }
        .file-audio {
            width: 100%;
            margin: 10px 0;
        }
        .file-video {
            max-width: 400px;
            max-height: 225px;
            border-radius: 5px;
        }
        .file-actions {
            margin-top: 10px;
        }
        .file-btn {
            padding: 8px 15px;
            margin: 5px;
            border: none;
            background: #4facfe;
            color: white;
            border-radius: 5px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            font-size: 0.9em;
        }
        .file-btn:hover {
            background: #3a8fd9;
        }
        .file-info {
            margin: 10px 0;
            padding: 10px;
            background: #f1f3f4;
            border-radius: 5px;
            font-family: monospace;
            font-size: 0.9em;
            word-break: break-all;
        }
        .login-container {
            max-width: 400px;
            margin: 100px auto;
            padding: 40px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center;
        }
        .password-input {
            width: 100%;
            padding: 15px;
            margin: 20px 0;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 1.1em;
        }
        .login-btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.3s;
        }
        .login-btn:hover {
            transform: translateY(-2px);
        }
        .error {
            color: #dc3545;
            margin-top: 10px;
        }
        .no-files {
            text-align: center;
            padding: 40px;
            color: #666;
            font-size: 1.2em;
        }
        .file-icon {
            font-size: 3em;
            margin: 15px 0;
        }
        .search-box {
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }
        .search-input {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 1em;
        }
        .filter-buttons {
            display: flex;
            gap: 10px;
            margin-top: 10px;
            flex-wrap: wrap;
        }
        .filter-btn {
            padding: 8px 15px;
            border: 2px solid #dee2e6;
            background: white;
            border-radius: 5px;
            cursor: pointer;
        }
        .filter-btn.active {
            background: #4facfe;
            color: white;
            border-color: #4facfe;
        }
    </style>
</head>
<body>
    {% if not logged_in %}
    <div class="login-container">
        <h1>🔐 Админ-панель</h1>
        <p>Введите пароль для доступа</p>
        <form method="post" action="/login">
            <input type="password" name="password" class="password-input" 
                   placeholder="Введите пароль" required>
            <button type="submit" class="login-btn">Войти</button>
            {% if error %}
            <div class="error">{{ error }}</div>
            {% endif %}
        </form>
    </div>
    {% else %}
    <div class="container">
        <header>
            <h1>🕰️ Time Capsule Bot - Admin Panel</h1>
            <p class="subtitle">Всего капсул: {{ stats.total }} | Файлов: {{ stats.files_count }}</p>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Всего капсул</div>
                <div class="stat-number">{{ stats.total }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Доставлено</div>
                <div class="stat-number">{{ stats.sent }}</div>
                <div class="stat-label">{{ stats.sent_percent }}%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Файлов</div>
                <div class="stat-number">{{ stats.files_count }}</div>
                <div class="stat-label">{{ stats.files_size }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Пользователей</div>
                <div class="stat-number">{{ stats.users_count }}</div>
                <div class="stat-label">уникальных</div>
            </div>
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="showTab('capsules')">📋 Капсулы</button>
            <button class="tab" onclick="showTab('files')">📁 Файлы</button>
            <button class="tab" onclick="showTab('stats')">📊 Статистика</button>
        </div>
        
        <!-- Вкладка Капсулы -->
        <div id="capsules" class="tab-content content-active">
            <div class="search-box">
                <input type="text" class="search-input" placeholder="Поиск по ID, тексту или пользователю..." 
                       onkeyup="searchCapsules(this.value)">
                <div class="filter-buttons">
                    <button class="filter-btn active" onclick="filterCapsules('all')">Все</button>
                    <button class="filter-btn" onclick="filterCapsules('pending')">Ожидают</button>
                    <button class="filter-btn" onclick="filterCapsules('sent')">Доставлены</button>
                    <button class="filter-btn" onclick="filterCapsules('with_files')">С файлами</button>
                </div>
            </div>
            
            <div id="capsulesContainer">
                {% for cap in capsules %}
                <div class="capsule {% if cap.is_sent %}delivered{% else %}pending{% endif %}" 
                     data-id="{{ cap.id }}" 
                     data-sender="{{ cap.sender_id }}" 
                     data-receiver="{{ cap.receiver_id }}"
                     data-text="{{ cap.message_text|lower if cap.message_text else '' }}"
                     data-sent="{{ cap.is_sent }}"
                     data-has-file="{{ 'true' if cap.has_file else 'false' }}">
                    
                    <div class="capsule-header">
                        <div>
                            <span class="capsule-id">#{{ cap.id }}</span>
                            <span style="color: #666; font-size: 0.9em;">{{ cap.created_at }}</span>
                        </div>
                        <div>
                            {% if cap.is_sent %}
                            <span style="color: #28a745;">✅ Доставлено</span>
                            {% else %}
                            <span style="color: #ffc107;">⏳ Ожидает ({{ cap.days_left }})</span>
                            {% endif %}
                        </div>
                    </div>
                    
                    <div class="capsule-users">
                        <span class="user-badge sender">👤 От: {{ cap.sender_id }}</span>
                        <span class="user-badge receiver">👥 Кому: {{ cap.receiver_id }}</span>
                    </div>
                    
                    {% if cap.message_text %}
                    <div class="capsule-text">
                        <strong>Сообщение:</strong><br>
                        {{ cap.message_text }}
                    </div>
                    {% endif %}
                    
                    {% if cap.has_file %}
                    <div class="file-preview">
                        <strong>📁 Файл:</strong> {{ cap.file_name }}
                        {% if cap.file_path and cap.file_path.endswith(('.jpg', '.jpeg', '.png', '.gif')) %}
                        <div style="margin-top: 10px;">
                            <img src="/view_file/{{ cap.id }}" class="file-image" alt="Preview">
                        </div>
                        {% endif %}
                        
                        <div class="file-actions">
                            <a href="/download_file/{{ cap.id }}" class="file-btn">⬇️ Скачать</a>
                            <a href="/view_file/{{ cap.id }}" target="_blank" class="file-btn">👁️ Просмотреть</a>
                            {% if cap.file_path %}
                            <span class="file-btn" style="background: #6c757d;">📦 {{ cap.file_size }}</span>
                            {% endif %}
                        </div>
                        
                        {% if cap.file_path %}
                        <div class="file-info">
                            Путь: {{ cap.file_path }}<br>
                            Telegram ID: {{ cap.telegram_file_id or 'нет' }}
                        </div>
                        {% endif %}
                    </div>
                    {% endif %}
                    
                    <div class="capsule-meta">
                        <span class="meta-item">📅 {{ cap.send_date }}</span>
                        <span class="meta-item">📊 {{ cap.message_type }}</span>
                        <span class="meta-item">🆔 #{{ cap.id }}</span>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <!-- Вкладка Файлы -->
        <div id="files" class="tab-content">
            <div class="search-box">
                <input type="text" class="search-input" placeholder="Поиск файлов..." 
                       onkeyup="searchFiles(this.value)">
                <div class="filter-buttons">
                    <button class="filter-btn active" onclick="filterFiles('all')">Все</button>
                    <button class="filter-btn" onclick="filterFiles('photo')">📸 Фото</button>
                    <button class="filter-btn" onclick="filterFiles('voice')">🎤 Голосовые</button>
                    <button class="filter-btn" onclick="filterFiles('video')">🎥 Видео</button>
                </div>
            </div>
            
            <div id="filesContainer">
                {% if files %}
                    {% for file in files %}
                    <div class="file-item" data-type="{{ file.file_type }}" data-name="{{ file.file_name|lower }}">
                        <div class="capsule-header">
                            <div>
                                <span class="capsule-id">📁 {{ file.file_name }}</span>
                                <span style="color: #666; font-size: 0.9em;">Капсула #{{ file.capsule_id }}</span>
                            </div>
                            <div>
                                <span style="color: #6c757d;">📦 {{ file.file_size }}</span>
                            </div>
                        </div>
                        
                        <div class="capsule-users">
                            <span class="user-badge">👤 От: {{ file.sender_id }}</span>
                            <span class="user-badge">👥 Для: {{ file.receiver_id }}</span>
                            <span class="user-badge">📅 {{ file.send_date }}</span>
                        </div>
                        
                        {% if file.file_path %}
                        <div class="file-preview">
                            {% if file.file_type == 'photo' %}
                            <img src="/view_file/{{ file.capsule_id }}" class="file-image" alt="{{ file.file_name }}">
                            {% elif file.file_type == 'voice' %}
                            <div class="file-icon">🎤</div>
                            <audio controls class="file-audio">
                                <source src="/download_file/{{ file.capsule_id }}" type="audio/ogg">
                                Ваш браузер не поддерживает аудио
                            </audio>
                            {% elif file.file_type == 'video' %}
                            <video controls class="file-video">
                                <source src="/download_file/{{ file.capsule_id }}" type="video/mp4">
                                Ваш браузер не поддерживает видео
                            </video>
                            {% else %}
                            <div class="file-icon">📄</div>
                            {% endif %}
                            
                            <div class="file-actions">
                                <a href="/download_file/{{ file.capsule_id }}" class="file-btn">⬇️ Скачать</a>
                                <a href="/view_file/{{ file.capsule_id }}" target="_blank" class="file-btn">👁️ Просмотреть</a>
                                <a href="javascript:void(0)" onclick="deleteFile({{ file.capsule_id }})" 
                                   class="file-btn" style="background: #dc3545;">🗑️ Удалить</a>
                            </div>
                            
                            <div class="file-info">
                                Путь: {{ file.file_path }}<br>
                                Тип: {{ file.file_type }} | Размер: {{ file.file_size }}
                            </div>
                        </div>
                        {% endif %}
                    </div>
                    {% endfor %}
                {% else %}
                    <div class="no-files">
                        <div class="file-icon">📭</div>
                        <p>Нет сохраненных файлов</p>
                        <p style="font-size: 0.9em; color: #999;">Пользователи еще не отправляли файлы</p>
                    </div>
                {% endif %}
            </div>
        </div>
        
        <!-- Вкладка Статистика -->
        <div id="stats" class="tab-content">
            <div style="padding: 30px;">
                <h2>📊 Подробная статистика</h2>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px;">
                    <div class="stat-card">
                        <div class="stat-label">Общий размер файлов</div>
                        <div class="stat-number">{{ stats.total_file_size }}</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-label">Средний размер файла</div>
                        <div class="stat-number">{{ stats.avg_file_size }}</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-label">Файлов на капсулу</div>
                        <div class="stat-number">{{ stats.files_per_capsule }}</div>
                    </div>
                </div>
                
                <div style="margin-top: 30px;">
                    <h3>📈 Распределение по типам:</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px;">
                        {% for type, count in stats.file_types.items() %}
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
                            <strong>{{ type }}</strong>: {{ count }} файлов
                        </div>
                        {% endfor %}
                    </div>
                </div>
                
                <div style="margin-top: 30px;">
                    <h3>👥 Топ отправителей:</h3>
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-top: 15px;">
                        {% for user in stats.top_senders %}
                        <div style="padding: 10px; border-bottom: 1px solid #dee2e6;">
                            👤 ID: {{ user.sender_id }} - {{ user.count }} капсул
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function showTab(tabName) {
            // Скрыть все вкладки
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('content-active');
            });
            
            // Показать выбранную
            document.getElementById(tabName).classList.add('content-active');
            
            // Обновить активные кнопки
            document.querySelectorAll('.tab').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
        }
        
        function searchCapsules(query) {
            const capsules = document.querySelectorAll('#capsulesContainer .capsule');
            query = query.toLowerCase();
            
            capsules.forEach(capsule => {
                const id = capsule.dataset.id;
                const sender = capsule.dataset.sender;
                const receiver = capsule.dataset.receiver;
                const text = capsule.dataset.text;
                
                const match = id.includes(query) || 
                             sender.includes(query) || 
                             receiver.includes(query) ||
                             text.includes(query);
                
                capsule.style.display = match ? 'block' : 'none';
            });
        }
        
        function filterCapsules(type) {
            const capsules = document.querySelectorAll('#capsulesContainer .capsule');
            const buttons = document.querySelectorAll('#capsules .filter-btn');
            
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            capsules.forEach(capsule => {
                let show = true;
                
                if (type === 'pending' && capsule.dataset.sent === 'True') show = false;
                if (type === 'sent' && capsule.dataset.sent === 'False') show = false;
                if (type === 'with_files' && capsule.dataset.hasFile === 'false') show = false;
                
                capsule.style.display = show ? 'block' : 'none';
            });
        }
        
        function searchFiles(query) {
            const files = document.querySelectorAll('#filesContainer .file-item');
            query = query.toLowerCase();
            
            files.forEach(file => {
                const name = file.dataset.name;
                const type = file.dataset.type;
                
                const match = name.includes(query) || type.includes(query);
                file.style.display = match ? 'block' : 'none';
            });
        }
        
        function filterFiles(type) {
            const files = document.querySelectorAll('#filesContainer .file-item');
            const buttons = document.querySelectorAll('#files .filter-btn');
            
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            files.forEach(file => {
                let show = true;
                
                if (type !== 'all' && file.dataset.type !== type) {
                    show = false;
                }
                
                file.style.display = show ? 'block' : 'none';
            });
        }
        
        function deleteFile(capsuleId) {
            if (confirm('Удалить этот файл? Это не удалит капсулу, только файл.')) {
                fetch(`/delete_file/${capsuleId}`, { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Файл удален');
                            location.reload();
                        } else {
                            alert('Ошибка: ' + data.error);
                        }
                    });
            }
        }
        
        // Показываем вкладку капсул по умолчанию
        showTab('capsules');
    </script>
    {% endif %}
</body>
</html>
'''

# Подключение к базе
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Форматирование размера файла
def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

# Дней до доставки
def days_left(sdate):
    try:
        send_date = datetime.strptime(sdate, '%Y-%m-%d')
        days = (send_date - datetime.now()).days
        if days < 0: return "просрочено"
        if days == 0: return "сегодня"
        if days == 1: return "завтра"
        return f"через {days} дн."
    except:
        return "—"

# Главная страница
@app.route('/', methods=['GET', 'POST'])
def index():
    # Проверка аутентификации
    logged_in = request.cookies.get('logged_in') == 'true'
    
    if request.method == 'POST' and not logged_in:
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            logged_in = True
        else:
            return render_template_string(HTML, logged_in=False, error="❌ Неверный пароль!")
    
    if not logged_in:
        return render_template_string(HTML, logged_in=False)
    
    # Получаем статистику
    conn = get_db()
    cursor = conn.cursor()
    
    # Общая статистика
    cursor.execute('SELECT COUNT(*) FROM capsules')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM capsules WHERE is_sent = 1')
    sent = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM capsules WHERE file_path IS NOT NULL AND file_path != ""')
    files_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT sender_id) FROM capsules')
    users_count = cursor.fetchone()[0]
    
    # Статистика файлов
    cursor.execute('SELECT file_path FROM capsules WHERE file_path IS NOT NULL AND file_path != ""')
    files = cursor.fetchall()
    
    total_size = 0
    for file in files:
        try:
            if os.path.exists(file['file_path']):
                total_size += os.path.getsize(file['file_path'])
        except:
            pass
    
    # Типы файлов
    cursor.execute('''
    SELECT message_type, COUNT(*) as count 
    FROM capsules 
    WHERE message_type IN ('photo', 'voice', 'video') 
    GROUP BY message_type
    ''')
    file_types = {row['message_type']: row['count'] for row in cursor.fetchall()}
    
    # Топ отправителей
    cursor.execute('''
    SELECT sender_id, COUNT(*) as count 
    FROM capsules 
    GROUP BY sender_id 
    ORDER BY count DESC 
    LIMIT 10
    ''')
    top_senders = cursor.fetchall()
    
    # Последние 50 капсул
    cursor.execute('''
    SELECT id, sender_id, receiver_id, message_type, message_text, 
           file_id, file_path, send_date, created_at, is_sent
    FROM capsules 
    ORDER BY created_at DESC 
    LIMIT 50
    ''')
    
    capsules_data = []
    for row in cursor.fetchall():
        cap = dict(row)
        cap['days_left'] = days_left(cap['send_date'])
        cap['has_file'] = bool(cap['file_path'])
        
        if cap['file_path']:
            cap['file_name'] = os.path.basename(cap['file_path'])
            try:
                cap['file_size'] = format_size(os.path.getsize(cap['file_path']))
            except:
                cap['file_size'] = "неизвестно"
        else:
            cap['file_name'] = None
            cap['file_size'] = None
        
        capsules_data.append(cap)
    
    # Все файлы для вкладки файлов
    cursor.execute('''
    SELECT id as capsule_id, sender_id, receiver_id, message_type, 
           file_path, send_date, created_at
    FROM capsules 
    WHERE file_path IS NOT NULL AND file_path != ''
    ORDER BY created_at DESC
    ''')
    
    files_data = []
    for row in cursor.fetchall():
        file_info = dict(row)
        if file_info['file_path'] and os.path.exists(file_info['file_path']):
            file_info['file_name'] = os.path.basename(file_info['file_path'])
            file_info['file_size'] = format_size(os.path.getsize(file_info['file_path']))
            file_info['file_type'] = file_info['message_type']
            files_data.append(file_info)
    
    conn.close()
    
    # Подготавливаем статистику
    stats = {
        'total': total,
        'sent': sent,
        'sent_percent': round((sent / total * 100) if total > 0 else 0, 1),
        'files_count': files_count,
        'files_size': format_size(total_size),
        'total_file_size': format_size(total_size),
        'avg_file_size': format_size(total_size / files_count if files_count > 0 else 0),
        'files_per_capsule': round(files_count / total, 2) if total > 0 else 0,
        'users_count': users_count,
        'file_types': file_types,
        'top_senders': top_senders
    }
    
    response = app.make_response(render_template_string(
        HTML, logged_in=True, stats=stats, capsules=capsules_data, files=files_data
    ))
    
    if logged_in:
        response.set_cookie('logged_in', 'true', max_age=60*60*24*7)  # 7 дней
    
    return response

# Просмотр файла
@app.route('/view_file/<int:capsule_id>')
def view_file(capsule_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT file_path, message_type FROM capsules WHERE id = ?', (capsule_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result or not result['file_path'] or not os.path.exists(result['file_path']):
        return "Файл не найден", 404
    
    file_path = result['file_path']
    
    # Определяем MIME-тип
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        if result['message_type'] == 'voice':
            mime_type = 'audio/ogg'
        elif result['message_type'] == 'video':
            mime_type = 'video/mp4'
        else:
            mime_type = 'application/octet-stream'
    
    return send_file(file_path, mimetype=mime_type)

# Скачивание файла
@app.route('/download_file/<int:capsule_id>')
def download_file(capsule_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT file_path FROM capsules WHERE id = ?', (capsule_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result or not result['file_path'] or not os.path.exists(result['file_path']):
        return "Файл не найден", 404
    
    file_path = result['file_path']
    file_name = os.path.basename(file_path)
    
    return send_file(file_path, as_attachment=True, download_name=file_name)

# Удаление файла
@app.route('/delete_file/<int:capsule_id>', methods=['POST'])
def delete_file(capsule_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT file_path FROM capsules WHERE id = ?', (capsule_id,))
    result = cursor.fetchone()
    
    if not result or not result['file_path']:
        conn.close()
        return jsonify({'success': False, 'error': 'Файл не найден в базе'})
    
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

# Логин
@app.route('/login', methods=['POST'])
def login():
    password = request.form.get('password', '')
    
    if password == ADMIN_PASSWORD:
        response = app.make_response('<script>window.location="/"</script>')
        response.set_cookie('logged_in', 'true', max_age=60*60*24*7)
        return response
    else:
        return render_template_string(HTML, logged_in=False, error="❌ Неверный пароль!")

# Выход
@app.route('/logout')
def logout():
    response = app.make_response('<script>window.location="/"</script>')
    response.set_cookie('logged_in', '', expires=0)
    return response

# Запуск
if __name__ == '__main__':
    print("=" * 50)
    print("🔧 Админ-панель Time Capsule Bot")
    print("=" * 50)
    print(f"🗄️  База данных: {DB_PATH}")
    print(f"📁 Папка медиа: {MEDIA_PATH}")
    print(f"🔐 Пароль: {ADMIN_PASSWORD}")
    print("=" * 50)
    
    # Проверяем папку media
    if not os.path.exists(MEDIA_PATH):
        print("⚠️  Папка media не найдена, создаю...")
        os.makedirs(MEDIA_PATH)
    
    # Запускаем сервер
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Админ-панель доступна на порту: {port}")
    print("🚀 Запуск...")
    
    app.run(host='0.0.0.0', port=port, debug=False)
