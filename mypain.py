from flask import Flask, jsonify, request
import os
import json

app = Flask(__name__)

DATA_FILE = 'players.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except:
            return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Qeydiyyat</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: Arial, sans-serif; }
        body { background-color: #05020a; color: #fff; height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 20px; }
        .card { background: #1a0000; border: 2px solid #ff3300; padding: 20px; border-radius: 10px; width: 100%; max-width: 350px; text-align: center; box-shadow: 0 0 15px rgba(255, 51, 0, 0.4); }
        h2 { color: #ffcc00; margin-bottom: 15px; }
        input { width: 100%; padding: 12px; margin: 8px 0; background: #000; border: 1px solid #ff6600; color: #fff; border-radius: 5px; text-align: center; outline: none; }
        button { background: #ff3300; color: #fff; border: none; padding: 12px; font-weight: bold; border-radius: 5px; cursor: pointer; width: 100%; margin-top: 10px; font-size: 16px; }
    </style>
</head>
<body>

    <div class="card" id="regCard">
        <h2>Oyunçu Qeydiyyatı</h2>
        <input type="text" id="nameInput" placeholder="Adınız">
        <input type="email" id="emailInput" placeholder="Gmail ünvanınız">
        <button onclick="registerPlayer()">Qeydiyyatdan Keç</button>
    </div>

    <div class="card" id="successCard" style="display:none;">
        <h2 style="color: #27ae60;">Uğurludur!</h2>
        <p>Şifrə kodunuz:</p>
        <div id="codeBox" style="font-size: 32px; font-weight: bold; color: #ffcc00; margin: 15px 0;"></div>
        <p style="font-size: 13px; color: #aaa; margin-bottom: 15px;">Bu kodu yadda saxlayın!</p>
        <button onclick="goToGame()">Oyuna Keç</button>
    </div>

    <script>
        async function registerPlayer() {
            let name = document.getElementById('nameInput').value.trim().toUpperCase();
            let email = document.getElementById('emailInput').value.trim().toLowerCase();
            
            if (!name || !email) { 
                alert("Ad və Gmail-i daxil edin!"); 
                return; 
            }

            let code = Math.floor(1000 + Math.random() * 9000).toString();

            try {
                let response = await fetch('/get_data');
                let players = await response.json();

                players[name] = { email: email, code: code, balance: 0.00 };

                let saveRes = await fetch('/save_data', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(players)
                });

                if (saveRes.ok) {
                    document.getElementById('regCard').style.display = 'none';
                    document.getElementById('successCard').style.display = 'block';
                    document.getElementById('codeBox').innerText = code;
                } else {
                    alert("Xəta baş verdi, yenidən sınayın.");
                }
            } catch (e) {
                alert("Serverlə əlaqə qurulmadı!");
            }
        }

        function goToGame() {
            alert("Oyun səhifəsinə keçid edilir!");
        }
    </script>
</body>
</html>
    '''

@app.route('/get_data')
def get_data():
    return jsonify(load_data())

@app.route('/save_data', methods=['POST'])
def save_players():
    data = request.json
    if data:
        save_data(data)
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
