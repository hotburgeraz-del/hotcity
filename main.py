from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Nümunəvi oyunçu bazası
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

@app.route('/admin')
def admin_panel():
    return render_template('admin.html', players=players_db.values())

@app.route('/api/set_next_win', methods=['POST'])
def set_next_win():
    data = request.json
    player_id = data.get('player_id')
    forced_win = data.get('next_win')
    
    if player_id in players_db:
        try:
            players_db[player_id]['next_win'] = float(forced_win)
            # Sintaksis xətasını aradan qaldırmaq üçün f-string sadələşdirildi:
            msg = "ugurla teyin edildi"
            return jsonify({"success": True, "message": msg})
        except ValueError:
            return jsonify({"success": False, "message": "Yanlis mebleg formati!"}), 400
            
    return jsonify({"success": False, "message": "Oyunçu tapılmadı!"}), 404

@app.route('/api/spin', methods=['POST'])
def spin():
    data = request.json
    player_id = data.get('player_id')
    
    if player_id not in players_db:
        return jsonify({"success": False, "message": "Oyunçu tapılmadı!"}), 404
        
    player = players_db[player_id]
    
    if player['next_win'] is not None:
        win_amount = player['next_win']
        player['next_win'] = None 
    else:
        win_amount = 0.0 
        
    player['balance'] += win_amount
    
    return jsonify({
        "success": True,
        "win_amount": win_amount,
        "new_balance": player['balance']
    })

if __name__ == '__main__':
    app.run(debug=True)