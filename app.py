from flask import Flask, request, jsonify, send_file
from tracker import log_attempt, get_stats, get_blocklist, get_recent_logs
import threading
import random
import time

app = Flask(__name__)

open("logs.txt", "w").close()
open("blocklist.txt", "w").close()

@app.route("/")
def dashboard():
    return send_file("dashboard.html")

@app.route("/attempt", methods=["POST"])
def attempt():
    data = request.json
    ip = data.get("ip")
    success = data.get("success")

    if ip is None or success is None:
        return jsonify({"error": "Missing IP or success field"}), 400

    result = log_attempt(ip, success)
    return jsonify(result)

@app.route("/stats", methods=["GET"])
def stats():
    return jsonify(get_stats())

@app.route("/blocklist", methods=["GET"])
def blocklist():
    return jsonify(get_blocklist())

@app.route("/recent-logs", methods=["GET"])
def recent_logs():
    return jsonify(get_recent_logs())

@app.route("/simulate-burst", methods=["POST"])
def simulate_burst():
    thread = threading.Thread(target=run_simulation)
    thread.start()
    return jsonify({"status": "started", "message": "Running 200 simulated logins."})

def run_simulation():
    test_ips = [f"192.168.0.{i}" for i in range(1, 6)]
    for _ in range(200):
        ip = random.choice(test_ips)
        success = random.random() > (0.1 if ip == "192.168.0.1" else 0.5)
        log_attempt(ip, success)
        time.sleep(random.uniform(0.1, 1.5))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)

