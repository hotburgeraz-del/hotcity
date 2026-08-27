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
    <title>Hell Hot Slot & Qeydiyyat</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: Arial, sans-serif; }
        body { background-color: #05020a; color: #fff; min-height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 10px; }
        .card { background: #1a0000; border: 2px solid #ff3300; padding: 20px; border-radius: 10px; width: 100%; max-width: 400px; text-align: center; box-shadow: 0 0 15px rgba(255, 51, 0, 0.4); }
        h2 { color: #ffcc00; margin-bottom: 15px; }
        input { width: 100%; padding: 12px; margin: 8px 0; background: #000; border: 1px solid #ff6600; color: #fff; border-radius: 5px; text-align: center; outline: none; }
        button { background: #ff3300; color: #fff; border: none; padding: 12px; font-weight: bold; border-radius: 5px; cursor: pointer; width: 100%; margin-top: 10px; font-size: 16px; }
        button:hover { background: #ff5522; }
        .slot-container { display: none; width: 100%; max-width: 450px; background: #110000; border: 2px solid #ffcc00; border-radius: 12px; padding: 15px; text-align: center; box-shadow: 0 0 20px rgba(255, 204, 0, 0.3); }
        .reels { display: flex; justify-content: space-around; background: #000; border: 2px solid #ff3300; border-radius: 8px; padding: 10px; margin: 15px 0; }
        .reel { font-size: 36px; background: #1a0000; width: 60px; height: 70px; display: flex; align-items: center; justify-content: center; border-radius: 5px; border: 1px solid #ff6600; }
        .info-panel { display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 15px; color: #ffcc00; font-weight: bold; }
    </style>
</head>
<body>

    <!-- QEYDİYYAT EKRANI -->
    <div class="card" id="regCard">
        <h2>Oyunçu Qeydiyyatı</h2>
        <input type="text" id="nameInput" placeholder="Adınız">
        <input type="email" id="emailInput" placeholder="Gmail ünvanınız">
        <button onclick="registerPlayer()">Qeydiyyatdan Keç</button>
    </div>

    <!-- UĞUR / KOD EKRANI -->
    <div class="card" id="successCard" style="display:none;">
        <h2 style="color: #27ae60;">Uğurludur!</h2>
        <p>Şifrə kodunuz:</p>
        <div id="codeBox" style="font-size: 32px; font-weight: bold; color: #ffcc00; margin: 15px 0;"></div>
        <p style="font-size: 13px; color: #aaa; margin-bottom: 15px;">Bu kodu yadda saxlayın!</p>
        <button onclick="showGame()">Oyuna Keç</button>
    </div>

    <!-- OYUN (SLOT) EKRANI -->
    <div class="slot-container" id="gameCard">
        <h2>HELL HOT 100</h2>
        <div class="info-panel">
            <span>Balans: $<span id="balanceVal">100.00</span></span>
            <span>Oyunçu: <span id="playerNameDisplay" style="color:#fff;"></span></span>
        </div>
        <div class="reels">
            <div class="reel" id="r1">🍒</div>
            <div class="reel" id="r2">🍋</div>
            <div class="reel" id="r3">🔔</div>
            <div class="reel" id="r4">7️⃣</div>
            <div class="reel" id="r5">🔥</div>
        </div>
        <input type="number" id="betInput" value="10" min="1" max="1000" style="margin-bottom: 10px;">
        <button onclick="spinReels()">FİRLƏD (SPİN)</button>
        <p id="winMsg" style="margin-top: 10px; color: #27ae60; font-weight: bold;"></p>
    </div>

    <script>
        let currentUser = "";
        let currentBalance = 100.00;

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

                players[name] = { email: email, code: code, balance: 100.00 };

                let saveRes = await fetch('/save_data', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(players)
                });

                if (saveRes.ok) {
                    currentUser = name;
                    currentBalance = 100.00;
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

        function showGame() {
            document.getElementById('successCard').style.display = 'none';
            document.getElementById('gameCard').style.display = 'block';
            document.getElementById('playerNameDisplay').innerText = currentUser;
            document.getElementById('balanceVal').innerText = currentBalance.toFixed(2);
        }

        async function spinReels() {
            let bet = parseFloat(document.getElementById('betInput').value);
            if (isNaN(bet) || bet <= 0) {
                alert(" düzgün məbləğ daxil edin!");
                return;
            }
            if (currentBalance < bet) {
                alert("Balansınızda kifayət qədər qalıq yoxdur!");
                return;
            }

            currentBalance -= bet;
            document.getElementById('balanceVal').innerText = currentBalance.toFixed(2);

            let symbols = ['🍒', '🍋', '🔔', '7️⃣', '🔥', '⭐', '🍇'];
            let r1 = symbols[Math.floor(Math.random() * symbols.length)];
            let r2 = symbols[Math.floor(Math.random() * symbols.length)];
            let r3 = symbols[Math.floor(Math.random() * symbols.length)];
            let r4 = symbols[Math.floor(Math.random() * symbols.length)];
            let r5 = symbols[Math.floor(Math.random() * symbols.length)];

            document.getElementById('r1').innerText = r1;
            document.getElementById('r2').innerText = r2;
            document.getElementById('r3').innerText = r3;
            document.getElementById('r4').innerText = r4;
            document.getElementById('r5').innerText = r5;

            let win = 0;
            if (r1 === r2 && r2 === r3) {
                win = bet * 5;
            } else if (r1 === r2 && r2 === r3 && r3 === r4) {
                win = bet * 20;
            } else if (r1 === r2 && r2 === r3 && r3 === r4 && r4 === r5) {
                win = bet * 100;
            }

            let msg = document.getElementById('winMsg');
            if (win > 0) {
                currentBalance += win;
                msg.style.color = "#27ae60";
                msg.innerText = `Təbriklər! $` + win + ` qazandınız!`;
            } else {
                msg.style.color = "#ff3300";
                msg.innerText = `Uduzdunuz, bir daha sınayın!`;
            }

            document.getElementById('balanceVal').innerText = currentBalance.toFixed(2);

            // Balansı serverə göndərək
            try {
                let res = await fetch('/get_data');
                let players = await res.json();
                if(players[currentUser]) {
                    players[currentUser].balance = currentBalance;
                    await fetch('/save_data', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(players)
                    });
                }
            } catch(e) {}
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

# --- ADMİN PANEL ---
@app.route('/admin')
def admin_panel():
    players = load_data()
    html = '''
    <!DOCTYPE html>
    <html lang="az">
    <head>
        <meta charset="UTF-8">
        <title>Admin Panel</title>
        <style>
            body { background: #111; color: #fff; font-family: Arial; padding: 20px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; background: #222; }
            th, td { border: 1px solid #444; padding: 10px; text-align: center; }
            th { background: #ff3300; color: #fff; }
            h1 { color: #ffcc00; }
        </style>
    </head>
    <body>
        <h1>Admin Panel - Qeydiyyatdan Keçənlər</h1>
        <table>
            <tr>
                <th>Ad</th>
                <th>Gmail</th>
                <th>Şifrə Kodu</th>
                <th>Balans</th>
            </tr>
    '''
    for name, info in players.items():
        html += f"<tr><td>{name}</td><td>{info.get('email')}</td><td style='color:#ffcc00; font-weight:bold;'>{info.get('code')}</td><td>${info.get('balance', 0):.2f}</td></tr>"
    
    html += '''
        </table>
    </body>
    </html>
    '''
    return html

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
