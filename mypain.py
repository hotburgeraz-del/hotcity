from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import urllib.parse

DB_FILE = "players_database.json"

if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

HTML_1 = """<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
    </div>
    <script>
        async function registerPlayer() {
            let name = document.getElementById('nameInput').value.trim().toUpperCase();
            let email = document.getElementById('emailInput').value.trim().toLowerCase();
            if (!name || !email) { alert("Ad və Gmail-i daxil edin!"); return; }
            let code = Math.floor(1000 + Math.random() * 9000).toString();
            try {
                let res = await fetch('/get_data');
                let players = await res.json();
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
                } else { alert("Xəta baş verdi!"); }
            } catch (e) { alert("Serverlə əlaqə yoxdur!"); }
        }
    </script>
</body>
</html>"""

HTML_ADMIN = """<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>Admin Panel</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: Arial, sans-serif; }
        body { background: #05020a; color: #fff; padding: 20px; }
        h2 { color: #ffcc00; margin-bottom: 15px; }
        .table-container { background: #1a0000; border: 2px solid #ff3300; border-radius: 8px; padding: 15px; overflow-x: auto; margin-top: 15px; }
        table { width: 100%; border-collapse: collapse; font-size: 14px; text-align: left; }
        th, td { border: 1px solid #440000; padding: 12px; color: #ddd; }
        th { background: #330000; color: #ffcc00; }
        button { background: #ff3300; color: #fff; border: none; padding: 8px 12px; font-weight: bold; border-radius: 4px; cursor: pointer; }
        .btn-green { background: #27ae60; }
    </style>
</head>
<body>
    <h2>Admin Panel</h2>
    <button class="btn-green" onclick="loadData()">Siyahını Yenilə</button>
    <div class="table-container">
        <table>
            <thead>
                <tr><th>Ad</th><th>Gmail</th><th>Kod</th><th>Balans</th><th>Əməliyyat</th></tr>
            </thead>
            <tbody id="tableBody"><tr><td colspan="5" style="text-align:center;">Yüklənir...</td></tr></tbody>
        </table>
    </div>
    <script>
        let globalPlayers = {};
        async function loadData() {
            let res = await fetch('/get_data');
            globalPlayers = await res.json();
            let tbody = document.getElementById('tableBody');
            tbody.innerHTML = '';
            let keys = Object.keys(globalPlayers);
            if (keys.length === 0) { tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;">Heç kim yoxdur.</td></tr>`; return; }
            keys.forEach(id => {
                let p = globalPlayers[id];
                tbody.innerHTML += `<tr><td><b>${id}</b></td><td>${p.email}</td><td style="color:#ffcc00;">${p.code}</td><td>₼${p.balance.toFixed(2)}</td><td><button class="btn-green" onclick="addBal('${id}')">+ Balans</button> <button onclick="delP('${id}')">Sil</button></td></tr>`;
            });
        }
        async function addBal(id) {
            let am = prompt("Məbləğ:", "10");
            if (!am) return;
            globalPlayers[id].balance += parseFloat(am);
            await save();
        }
        async function delP(id) {
            if (!confirm("Silinsin?")) return;
            delete globalPlayers[id];
            await save();
        }
        async function save() {
            await fetch('/save_data', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(globalPlayers) });
            loadData();
        }
        setInterval(loadData, 2000);
        loadData();
    </script>
</body>
</html>"""

class MasterServer(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path).path
        if parsed_path == "/" or parsed_path == "/1.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_1.encode("utf-8"))
        elif parsed_path == "/admin" or parsed_path == "/ADMIN%20PANEL.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_ADMIN.encode("utf-8"))
        elif parsed_path == "/get_data":
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            with open(DB_FILE, "r", encoding="utf-8") as f:
                self.wfile.write(f.read().encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path).path
        if parsed_path == "/save_data":
            length = int(self.headers['Content-Length'])
            data = self.rfile.read(length)
            with open(DB_FILE, "w", encoding="utf-8") as f:
                f.write(data.decode("utf-8"))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(('0.0.0.0', port), MasterServer)
    print(f"SERVER AKTİVDİR! Port: {port}")
    server.serve_forever()