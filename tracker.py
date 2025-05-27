import time
import sys
from collections import defaultdict, deque

FAIL_THRESHOLD = 3
LOG_FILE = "logs.txt"
BLOCKLIST_FILE = "blocklist.txt"

fail_streak = defaultdict(int)
total_attempts = 0
alerts_triggered = 0
unique_ips = set()
recent_attempt_timestamps = []
recent_logs = deque(maxlen=10)  # holds last 10 login attempts
last_seen = defaultdict(float)

def log_attempt(ip, success):
    global total_attempts, alerts_triggered
    now = time.time()
    recent_attempt_timestamps.append(now)

    # Soft rate limiting (tag, not block)
    rate_limited = False
    if now - last_seen[ip] < 2:
        rate_limited = True
    last_seen[ip] = now

    # Log to in-memory list for frontend
    recent_logs.append({
        "ip": ip,
        "success": success,
        "time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now)),
        "rate_limited": rate_limited
    })

    # Load blocklist
    with open(BLOCKLIST_FILE, "a+") as f:
        f.seek(0)
        blocked = set(line.strip() for line in f.readlines())
    
    if ip in blocked:
        return {
            "status": "ignored",
            "message": f"{ip} is already blocked."
        }

    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    result = "SUCCESS" if success else "FAILURE"
    log_entry = f"[{timestamp}] IP: {ip} - {result}"
    
    with open(LOG_FILE, "a") as f:
        f.write(log_entry + "\n")
    
    total_attempts += 1
    unique_ips.add(ip)

    if not success:
        fail_streak[ip] += 1
        if fail_streak[ip] == FAIL_THRESHOLD:
            alerts_triggered += 1
            with open(BLOCKLIST_FILE, "a") as f:
                f.write(f"{ip}\n")
            return {
                "status": "alert",
                "ip": ip,
                "message": f"{ip} blocked after {FAIL_THRESHOLD} failed attempts.",
                "rate_limited": rate_limited
            }
    else:
        fail_streak[ip] = 0

    return {
        "status": "logged",
        "ip": ip,
        "success": success,
        "streak": fail_streak[ip],
        "rate_limited": rate_limited
    }

def get_stats():
    now = time.time()
    # Count attempts in the last 2 seconds
    recent_attempts = [ts for ts in recent_attempt_timestamps if now - ts <= 2]
    return {
        "total_attempts": total_attempts,
        "alerts_triggered": alerts_triggered,
        "unique_ips": len(unique_ips),
        "recent_attempts": len(recent_attempts)
    }

def get_blocklist():
    try:
        with open(BLOCKLIST_FILE, "r") as f:
            return [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        return []

def get_recent_logs():
    return list(recent_logs)

def reset_tracker_state():
    global fail_streak, unique_ips, total_attempts, alerts_triggered, recent_attempt_timestamps
    fail_streak.clear()
    unique_ips.clear()
    total_attempts = 0
    alerts_triggered = 0
    recent_attempt_timestamps.clear()
    print("[TRACKER RESET] All internal state cleared.")

