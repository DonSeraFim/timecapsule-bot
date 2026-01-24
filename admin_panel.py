from flask import Flask, render_template_string, request
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

# Пароль для входа (ИЗМЕНИ НА СВОЙ!)
ADMIN_PASSWORD = "admin123"

# Пути
BASE_DIR = os.getcwd()
DB_PATH = os.path.join(BASE_DIR, 'capsules.db')

print(f"🔧 Админ-панель запущена!")
print(f"🗄️  База данных: {DB_PATH}")

# HTML шаблон
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>🕰️ Time Capsule Admin</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: Arial, sans-serif; 
            background: #f0f2f5;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        h1 { font-size: 2.5em; margin-bottom: 10px; }
        .stats { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px; 
            padding: 30px;
            background: #f8f9fa;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }
        .capsules {
            padding: 30px;
        }
        .capsule {
            background: white;
            border-left: 5px solid #667eea;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .capsule.delivered { border-left-color: #28a745; }
        .capsule.pending { border-left-color: #ffc107; }
        .capsule-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }
        .capsule-id {
            font-weight: bold;
            color: #667eea;
        }
        .capsule-users {
            display: flex;
            gap: 20px;
            margin: 10px 0;
        }
        .user-badge {
            background: #e9ecef;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.9em;
        }
        .capsule-text {
            margin: 15px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
        }
        .login-box {
            max-width: 400px;
            margin: 100px auto;
            padding: 40px;
            background: white;
            border-radius: 10px;
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
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1.1em;
            cursor: pointer;
        }
        .error { color: #dc3545; margin-top: 10px; }
    </style>
</head>
<body>
    {% if not logged_in %}
    <div class="login-box">
        <h1>🔐 Админ-панель</h1>
        <p>Введите пароль для доступа</p>
        <form method="post">
            <input type="password" name="password" class="password-input" 
                   placeholder="Пароль" required>
            <button type="submit" class="login-btn">Войти</button>
            {% if error %}
            <div class="error">{{ error }}</div>
            {% endif %}
        </form>
    </div>
    {% else %}
    <div class="container">
        <header>
            <h1>🕰️ Time Capsule Bot Admin</h1>
            <p>Всего капсул: {{ stats.total }} | Активных: {{ stats.active_users }}</p>
        </header>

        <div class="stats">
            <div class="stat-card">
                <div>Всего капсул</div>
                <div class="stat-number">{{ stats.total }}</div>
            </div>
            <div class="stat-card">
                <div>Доставлено</div>
                <div class="stat-number">{{ stats.sent }}</div>
                <div>{{ stats.sent_percent }}%</div>
            </div>
            <div class="stat-card">
                <div>Ожидают</div>
                <div class="stat-number">{{ stats.pending }}</div>
                <div>{{ stats.pending_percent }}%</div>
            </div>
            <div class="stat-card">
                <div>Сегодня</div>
                <div class="stat-number">{{ stats.today }}</div>
                <div>к доставке</div>
            </div>
        </div>

        <div class="capsules">
            <h2>📋 Последние капсулы</h2>
            {% for cap in capsules %}
            <div class="capsule {% if cap.is_sent %}delivered{% else %}pending{% endif %}">
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
                    <span class="user-badge">👤 От: {{ cap.sender_id }}</span>
                    <span class="user-badge">👥 Кому: {{ cap.receiver_id }}</span>
                </div>

                {% if cap.message_text %}
                <div class="capsule-text">
                    <strong>Сообщение:</strong><br>
                    {{ cap.message_text }}
                </div>
                {% endif %}

                <div style="margin-top: 10px;">
                    <span style="background: #e9ecef; padding: 5px 10px; border-radius: 3px; font-size: 0.9em;">
                        📅 {{ cap.send_date }}
                    </span>
                    <span style="background: #e9ecef; padding: 5px 10px; border-radius: 3px; font-size: 0.9em; margin-left: 10px;">
                        📊 {{ cap.message_type }}
                    </span>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}
</body>
</html>
'''


# Подключение к базе
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


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
    # Проверка пароля
    if 'logged_in' not in request.cookies or request.cookies.get('logged_in') != 'true':
        logged_in = False

        if request.method == 'POST':
            password = request.form.get('password', '')
            if password == ADMIN_PASSWORD:
                logged_in = True
            else:
                return render_template_string(HTML, logged_in=False, error="❌ Неверный пароль!")
    else:
        logged_in = True

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

    cursor.execute('SELECT COUNT(*) FROM capsules WHERE is_sent = 0')
    pending = cursor.fetchone()[0]

    # Уникальные пользователи
    cursor.execute('SELECT COUNT(DISTINCT sender_id) FROM capsules')
    active_users = cursor.fetchone()[0]

    # На сегодня
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('SELECT COUNT(*) FROM capsules WHERE send_date = ?', (today,))
    today_caps = cursor.fetchone()[0]

    # Проценты
    sent_percent = round((sent / total * 100) if total > 0 else 0, 1)
    pending_percent = round((pending / total * 100) if total > 0 else 0, 1)

    # Последние 20 капсул
    cursor.execute('''
    SELECT id, sender_id, receiver_id, message_type, message_text, 
           send_date, created_at, is_sent
    FROM capsules ORDER BY created_at DESC LIMIT 20
    ''')

    capsules = []
    for row in cursor.fetchall():
        cap = dict(row)
        cap['days_left'] = days_left(cap['send_date'])
        capsules.append(cap)

    conn.close()

    # Данные для шаблона
    stats = {
        'total': total,
        'sent': sent,
        'pending': pending,
        'sent_percent': sent_percent,
        'pending_percent': pending_percent,
        'active_users': active_users,
        'today': today_caps
    }

    response = app.make_response(render_template_string(
        HTML, logged_in=True, stats=stats, capsules=capsules
    ))

    if logged_in:
        response.set_cookie('logged_in', 'true', max_age=60 * 60 * 24)

    return response


# Запуск
if __name__ == '__main__':
    print(f"🌐 Админ-панель доступна по адресу: http://localhost:5000")
    print(f"🔐 Пароль для входа: {ADMIN_PASSWORD}")
    app.run(host='0.0.0.0', port=5000, debug=True)