from flask import Flask, request, jsonify
import os
import json

app = Flask(__name__)
DATA_FILE = 'players.json'

# Əgər players.json faylı yoxdursa, boş obyekt ilə yarat
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump({}, f)

@app.route('/get_data', methods=['GET'])
def get_data():
    with open(DATA_FILE, 'r') as f:
        try:
            data = json.load(f)
        except:
            data = {}
    return jsonify(data)

@app.route('/save_data', methods=['POST'])
def save_data():
    data = request.json
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)