import os
import threading

from flask import Flask, request, jsonify
from flask_cors import CORS

from tracker import AttackTracker
from simulate_api import run_simulation

app = Flask(__name__)
CORS(app)  # enable CORS for all routes

# Instantiate the tracker
tracker = AttackTracker()

# Path to store persistent blocklist entries
BLOCKLIST_PATH = os.path.join(os.getcwd(), 'blocklist.txt')

# In‐memory sets of blocked IPs and locked users
blocked_ips = set()
locked_users = set()

# Load any previously‐saved blocklist entries from file on startup
if os.path.exists(BLOCKLIST_PATH):
    with open(BLOCKLIST_PATH) as f:
        for line in f:
            line = line.strip()
            if line.startswith('IP:'):
                blocked_ips.add(line.split(':', 1)[1])
            elif line.startswith('USER:'):
                locked_users.add(line.split(':', 1)[1])


@app.route('/attempt', methods=['POST'])
def attempt():
    """
    Record a single login attempt. Returns JSON of the recorded event,
    and, if this IP/user is blocked, returns HTTP 403.
    """
    data = request.get_json() or {}
    ip = data.get('ip')
    user = str(data.get('user', ''))

    # Always record the attempt (even if blocked)
    record = tracker.record_attempt(
        ip=ip,
        user_id=user,
        geo=data.get('geo', ''),
        sim_type=data.get('sim_type', 'normal'),
        result='SUCCESS' if data.get('success') else 'FAILURE'
    )

    # If this record flagged a new block, persist it
    if record.get('is_blocked'):
        entry = None
        if record['sim_type'] in ('bruteforce', 'geohop'):
            # Block user (lock user account)
            if user not in locked_users:
                locked_users.add(user)
                entry = f"USER:{user}"
        else:
            # Block IP for credential‐stuffing or normal‐mode blocks
            if ip not in blocked_ips:
                blocked_ips.add(ip)
                entry = f"IP:{ip}"

        if entry:
            # Append to blocklist.txt so it’s persistent
            with open(BLOCKLIST_PATH, 'a') as bf:
                bf.write(entry + "\n")

    # If this IP or user is in the blockset, return 403
    if ip in blocked_ips:
        return jsonify({'error': 'IP blocked'}), 403
    if user in locked_users:
        return jsonify({'error': 'User locked'}), 403

    # Otherwise return the record as normal
    return jsonify(record), 200


@app.route('/stats', methods=['GET'])
def stats():
    """
    Return the aggregated stats (arrays for charting) plus the recent log feed.
    Shape:
      {
        attempts:   [ ... ],
        failures:   [ ... ],
        suspicions: [ ... ],
        blocks:     [ ... ],
        labels:     [ ... ],
        recent:     [ {timestamp, ip, user, geo, sim_type, result, is_suspicious, is_blocked}, ... ]
      }
    """
    payload = tracker.get_stats()
    payload['recent'] = tracker.get_recent()
    return jsonify(payload), 200


@app.route('/simulate', methods=['POST'])
def simulate():
    """
    Kick off a background thread to run a simulation of “sim_type” traffic.
    The thread will call /attempt on this same server repeatedly.
    """
    params = request.get_json() or {}
    sim_type   = params.get('sim_type',     'normal')
    rate       = params.get('rate',         0.1)
    duration   = params.get('duration',     60)
    failure_rt = params.get('failure_rate', 0.2)

    # Build the server URL (e.g. "http://localhost:5000")
    server_url = request.host_url.rstrip('/')

    # Start the background thread without blocking the request
    thread = threading.Thread(
        target=run_simulation,
        args=(sim_type, rate, duration, failure_rt, server_url),
        daemon=True
    )
    thread.start()

    return jsonify({'status': 'simulation started'}), 202


@app.route('/thresholds', methods=['GET'])
def get_thresholds():
    """
    Return the current threshold settings for brute‐force, geo‐hop, and cred‐stuff.
    The React dropdown will call this to populate its form fields.
    """
    return jsonify({
        "bruteforce_limit": tracker.BF_THRESHOLD,
        "geohop_interval":  tracker.GH_INTERVAL,
        "credstuff_limit":  tracker.CS_LIMIT
    }), 200


@app.route('/thresholds', methods=['POST'])
def post_thresholds():
    """
    Update the threshold values. React will POST an object like:
      { bruteforce_limit: 5, geohop_interval: 60, credstuff_limit: 10 }
    """
    data = request.get_json() or {}
    tracker.update_thresholds(
        bf=data.get("bruteforce_limit"),
        gh=data.get("geohop_interval"),
        cs=data.get("credstuff_limit")
    )
    return jsonify({"status": "thresholds updated"}), 200

@app.route('/blocklist', methods=['GET'])
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

    result = []
    for e in sorted(unique_entries):
        t, val = e.split(":", 1)
        result.append({"type": t, "value": val})

    return jsonify(result), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, threaded=True, debug=True)
