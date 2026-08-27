import json
import os
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
DATA_FILE = "players.json"


def load_players():
  if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
      try:
        return json.load(f)
      except:
        return {}
  return {}


def save_players(data):
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


# 1. OYUNÇU ÜÇÜN ƏSAS LİNK (Məsələn: http://127.0.0.1:5000/)
@app.route("/")
def index():
  return render_template("index.html")


# 2. ADMIN ÜÇÜN TAMAMİLƏ AYRI VƏ GİZLİ LİNK (Məsələn: http://127.0.0.1:5000/gizli-panel-999)
@app.route("/gizli-panel-999")
def admin_panel():
  return render_template("gizli_panel.html")


@app.route("/get_data", methods=["GET"])
def get_data():
  return jsonify(load_players())


@app.route("/save_data", methods=["POST"])
def save_data():
  try:
    new_data = request.json
    save_players(new_data)
    return jsonify({"status": "success"})
  except Exception as e:
    return jsonify({"status": "error", "message": str(e)}), 400


if __name__ == "__main__":
  app.run(host="127.0.0.1", port=5000, debug=True)