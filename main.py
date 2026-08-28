from flask import Flask, render_template, request, jsonify
import json
import os
import random
import time

app = Flask(__name__)
DATA_FILE = "players.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin_panel():
    return render_template('admin.html')

@app.route('/get_data', methods=['GET'])
def get_data():
    return jsonify(load_data())

@app.route('/save_data', methods=['POST'])
def save_data_route():
    data = request.json
    save_data(data)
    return jsonify({"status": "success"})

@app.route('/auth', methods=['POST'])
def auth():
    req = request.json
    name = req.get('name', 'Oyunçu').strip()
    gmail = req.get('gmail', '').strip()

    if not gmail or '@' not in gmail:
        return jsonify({"status": "error", "message": "Zəhmət olmasa etibarlı Gmail daxil edin!"})

    players = load_data()

    for p_id, p_info in players.items():
        if p_info.get('gmail') == gmail:
            p_info['last_active'] = int(time.time() * 1000)
            p_info['name'] = name
            save_data(players)
            return jsonify({
                "status": "success",
                "playerId": p_id,
                "balance": p_info['balance'],
                "code": p_info.get('code', '')
            })

    player_id = f"HOT_{random.randint(1000, 9999)}"
    while player_id in players:
        player_id = f"HOT_{random.randint(1000, 9999)}"
        
    secret_code = f"PASS{random.randint(100, 999)}"

    players[player_id] = {
        "name": name,
        "gmail": gmail,
        "balance": 10.00,
        "code": secret_code,
        "last_active": int(time.time() * 1000)
    }
    save_data(players)

    return jsonify({
        "status": "success",
        "playerId": player_id,
        "balance": 10.00,
        "code": secret_code
    })

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    req = request.json
    player_id = req.get('playerId')
    if not player_id:
        return jsonify({"status": "error"})
    
    players = load_data()
    if player_id in players:
        players[player_id]['last_active'] = int(time.time() * 1000)
        save_data(players)
        return jsonify({"status": "success"})
    return jsonify({"status": "not_found"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)