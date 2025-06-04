# app.py

import os
import threading

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask import send_from_directory

from tracker import AttackTracker
from simulate_api import run_simulation

app = Flask(__name__)
CORS(app)  # allow cross-origin requests

# ──────────────────────────────────────────────────────────────────────────────
# Instantiate the tracker
# ──────────────────────────────────────────────────────────────────────────────
tracker = AttackTracker()

# Path to store persistent blocklist entries
BLOCKLIST_PATH = os.path.join(os.getcwd(), "blocklist.txt")
LOGS_PATH = os.path.join(os.getcwd(), "logs.txt")

# In-memory sets for blocked IPs and locked users
blocked_ips = set()
locked_users = set()

# Load any previously-saved blocklist entries from file on startup
if os.path.exists(BLOCKLIST_PATH):
    with open(BLOCKLIST_PATH) as f:
        for line in f:
            line = line.strip()
            if line.startswith("IP:"):
                blocked_ips.add(line.split(":", 1)[1])
            elif line.startswith("USER:"):
                locked_users.add(line.split(":", 1)[1])


# ──────────────────────────────────────────────────────────────────────────────
# 1) /attempt endpoint (unchanged)
# ──────────────────────────────────────────────────────────────────────────────
@app.route("/attempt", methods=["POST"])
def attempt():
    data = request.get_json() or {}
    ip = data.get("ip")
    user = str(data.get("user", ""))

    # Always record the attempt (even if blocked)
    record = tracker.record_attempt(
        ip=ip,
        user_id=user,
        geo=data.get("geo", ""),
        sim_type=data.get("sim_type", "normal"),
        result="SUCCESS" if data.get("success") else "FAILURE",
    )

    # If this record flagged a new block, persist it
    if record.get("is_blocked"):
        entry = None
        if record["sim_type"] in ("bruteforce", "geohop"):
            # Block user (lock user account)
            if user not in locked_users:
                locked_users.add(user)
                entry = f"USER:{user}"
        else:
            # Block IP for credential-stuffing or normal-mode blocks
            if ip not in blocked_ips:
                blocked_ips.add(ip)
                entry = f"IP:{ip}"

        if entry:
            with open(BLOCKLIST_PATH, "a") as bf:
                bf.write(entry + "\n")

    # If this IP or user is in the blockset, return 403
    if ip in blocked_ips:
        return jsonify({"error": "IP blocked"}), 403
    if user in locked_users:
        return jsonify({"error": "User locked"}), 403

    # Otherwise return the record as normal
    return jsonify(record), 200


# ──────────────────────────────────────────────────────────────────────────────
# 2) /stats endpoint (unchanged)
# ──────────────────────────────────────────────────────────────────────────────
@app.route("/stats", methods=["GET"])
def stats():
    payload = tracker.get_stats()
    payload["recent"] = tracker.get_recent()
    return jsonify(payload), 200


# ──────────────────────────────────────────────────────────────────────────────
# 3) /simulate endpoint (unchanged)
# ──────────────────────────────────────────────────────────────────────────────
@app.route("/simulate", methods=["POST"])
def simulate():
    data = request.get_json() or {}
    sim_type = data.get("sim_type", "normal")
    delay = data.get("delay", 1.0)
    iterations = data.get("iterations", 30)
    failure_rt = data.get("failure_rate", 0.2)
    workers = data.get("workers", 1)

    server_url = request.host_url.rstrip("/")

    thread = threading.Thread(
        target=run_simulation,
        args=(sim_type, delay, iterations, failure_rt, server_url, workers),
        daemon=True,
    )
    thread.start()
    return jsonify({"status": "simulation started"}), 202


# ──────────────────────────────────────────────────────────────────────────────
# 4) Remove old /thresholds routes (NOT USED ANYMORE)
#    (React was calling /defense-thresholds, so we do not need /thresholds)
# ──────────────────────────────────────────────────────────────────────────────


# ──────────────────────────────────────────────────────────────────────────────
# 5) /blocklist endpoint (unchanged)
# ──────────────────────────────────────────────────────────────────────────────
@app.route("/blocklist", methods=["GET"])
def get_blocklist():
    unique_entries = set()
    if os.path.exists(BLOCKLIST_PATH):
        with open(BLOCKLIST_PATH) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(":", 1)
                if len(parts) != 2:
                    continue
                t, val = parts[0], parts[1]
                if t in ("IP", "USER"):
                    unique_entries.add(f"{t}:{val}")

    result = [{"type": e.split(":", 1)[0], "value": e.split(":", 1)[1]} for e in sorted(unique_entries)]
    return jsonify(result), 200


# ──────────────────────────────────────────────────────────────────────────────
# 6) /defense-thresholds GET + POST (correctly named, with ASCII hyphen)
# ──────────────────────────────────────────────────────────────────────────────
@app.route("/defense-thresholds", methods=["GET"])
def get_defense_thresholds():
    return jsonify(tracker.get_thresholds()), 200

@app.route("/defense-thresholds", methods=["POST"])
def post_defense_thresholds():
    data = request.get_json() or {}
    tracker.update_thresholds(
        brute_threshold = data.get("brute_threshold"),
        brute_window    = data.get("brute_window"),
        geohop_threshold= data.get("geohop_threshold"),
        cred_threshold  = data.get("cred_threshold"),
        cred_window     = data.get("cred_window"),
    )
    return jsonify({"status": "thresholds updated"}), 200

@app.route("/reset", methods=["POST"])
def reset():
    # 1) Clear the on-disk files
    open(LOGS_PATH, "w").close()
    open(BLOCKLIST_PATH, "w").close()

    # 2) Clear the in-memory blocklists & suspicious sets
    tracker.blocked_ips.clear()
    tracker.blocked_users.clear()
    tracker.suspicious_ips.clear()
    tracker.suspicious_users.clear()

    # 3) Clear the tracker’s live-feed records & time buckets
    tracker.records.clear()
    tracker.buckets.clear()
    tracker._start_new_bucket()

    return jsonify({"status": "reset complete"}), 200


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    # If the requested file exists in frontend-dist, serve it
    if path and os.path.exists(f"frontend-dist/{path}"):
        return send_from_directory("frontend-dist", path)
    # Otherwise, serve index.html (so React Router can work)
    return send_from_directory("frontend-dist", "index.html")


# ──────────────────────────────────────────────────────────────────────────────
# 7) Run Flask
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True, debug=True)
