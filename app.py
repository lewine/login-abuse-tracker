import os
import threading
from flask import Flask, request, jsonify, send_from_directory
from tracker import AttackTracker
from simulate_api import run_simulation

app = Flask(__name__, static_folder='static', template_folder='templates')
tracker = AttackTracker()

@app.route('/attempt', methods=['POST'])
def attempt():
    data = request.get_json()
    record = tracker.record_attempt(
        ip=data.get('ip'),
        user_id=data.get('user'),
        geo=data.get('geo', ''),
        sim_type=data.get('sim_type', 'normal'),
        result='SUCCESS' if data.get('success') else 'FAILURE'
    )
    return jsonify(record), 200

@app.route('/stats', methods=['GET'])
def stats():
    stats = tracker.get_stats()
    # include the most recent records so dashboard can slice off the top 20
    stats['recent'] = tracker.get_recent()
    return jsonify(stats), 200


@app.route('/recent', methods=['GET'])
def recent():
    return jsonify(tracker.get_recent()), 200

@app.route('/simulate', methods=['POST'])
def simulate():
    params = request.get_json() or {}
    sim_type = params.get('sim_type', 'normal')
    rate = params.get('rate', 0.1)
    duration = params.get('duration', 60)
    failure_rate = params.get('failure_rate', 0.2)
    # run simulation in background thread
    thread = threading.Thread(
        target=run_simulation,
        args=(sim_type, rate, duration, failure_rate),
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