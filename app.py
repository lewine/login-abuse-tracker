import os
import threading
from flask import Flask, request, jsonify, send_from_directory
from tracker import AttackTracker
from simulate_api import run_simulation

app = Flask(__name__, static_folder='static', template_folder='templates')
tracker = AttackTracker()
BLOCKLIST_PATH = os.path.join(os.getcwd(), 'blocklist.txt')

# Load persisted blocklist entries (IP and USER prefixes)
blocked_ips = set()
locked_users = set()
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
    data = request.get_json()
    ip = data.get('ip')
    user = str(data.get('user'))

    # Always record the attempt so live-feed shows even if blocked
    record = tracker.record_attempt(
        ip=ip,
        user_id=user,
        geo=data.get('geo', ''),
        sim_type=data.get('sim_type', 'normal'),
        result='SUCCESS' if data.get('success') else 'FAILURE'
    )

    # Persist new blocks to file & in-memory sets
    if record.get('is_blocked'):
        entry = None
        if record['sim_type'] in ('bruteforce', 'geohop'):
            if user not in locked_users:
                locked_users.add(user)
                entry = f"USER:{user}"

        else:
            if ip not in blocked_ips:
                blocked_ips.add(ip)
                entry = f"IP:{ip}"

        if entry:
            with open(BLOCKLIST_PATH, 'a') as bf:
                bf.write(entry)

    # After recording, enforce blocklist behavior for client
    if ip in blocked_ips:
        return jsonify({'error': 'IP blocked'}), 403
    if user in locked_users:
        return jsonify({'error': 'User locked'}), 403

    return jsonify(record), 200

@app.route('/stats', methods=['GET'])
def stats():
    stats = tracker.get_stats()
    stats['recent'] = tracker.get_recent()
    return jsonify(stats), 200

@app.route('/recent', methods=['GET'])
def recent():
    return jsonify(tracker.get_recent()), 200

@app.route('/blocked', methods=['GET'])
def blocked_records():
    recent = tracker.get_recent()
    blocked = [rec for rec in recent if rec.get('is_blocked')]
    return jsonify(blocked), 200

@app.route('/simulate', methods=['POST'])
def simulate():
    params     = request.get_json() or {}
    sim_type   = params.get('sim_type',    'normal')
    rate       = params.get('rate',        0.1)
    duration   = params.get('duration',    60)
    failure_rt = params.get('failure_rate',0.2)
    # Build a server_url that matches the actual host:port
    server_url = request.host_url.rstrip('/')  

    thread = threading.Thread(
        target=run_simulation,
        args=(sim_type, rate, duration, failure_rt, server_url),
        daemon=True
    )
    thread.start()
    return jsonify({'status': 'simulation started'}), 202


@app.route('/', methods=['GET'])
def dashboard():
    return send_from_directory('templates', 'dashboard.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, threaded=True, debug=True)
