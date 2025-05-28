import os
import json
import time
from collections import deque

# constants
WINDOW_SIZE = 2   # seconds per bucket
MAX_BUCKETS = 30  # keep ~1 minute of history

# file paths
BLOCKLIST_PATH = os.path.join(os.getcwd(), 'blocklist.txt')
LOGS_PATH = os.path.join(os.getcwd(), 'logs.txt')

class AttackTracker:
    def __init__(self):
        # start fresh: truncate logs and blocklist on startup
        open(LOGS_PATH, 'w').close()
        open(BLOCKLIST_PATH, 'w').close()
        self.blocked_ips = set()

        # live-feed queue (most recent records)
        self.records = deque(maxlen=1000)
        # time-series buckets for graph data
        self.buckets = deque(maxlen=MAX_BUCKETS)
        self._start_new_bucket()

    def _start_new_bucket(self):
        # align bucket start to WINDOW_SIZE boundary
        start_ts = int(time.time() // WINDOW_SIZE) * WINDOW_SIZE
        bucket = {
            'start': start_ts,
            'attempts': 0,
            'failures': 0,
            'suspicions': 0,
            'blocks': 0,
        }
        self.buckets.append(bucket)
        self.current_bucket = bucket

    def _roll_buckets(self):
        now = time.time()
        bucket_ts = int(now // WINDOW_SIZE) * WINDOW_SIZE
        if not self.buckets or bucket_ts != self.current_bucket['start']:
            self._start_new_bucket()

    def record_attempt(self, ip, user_id, geo, sim_type, result,
                       is_suspicious=False, is_blocked=False):
        # apply blocklist: if ip already blocked, override record
        if ip in self.blocked_ips:
            is_blocked = True
            is_suspicious = True

        # roll buckets and update stats
        self._roll_buckets()
        record = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
            'ip': ip,
            'user': user_id,
            'geo': geo,
            'sim_type': sim_type,
            'result': result,
            'is_suspicious': is_suspicious,
            'is_blocked': is_blocked,
        }
        b = self.current_bucket
        b['attempts'] += 1
        if result == 'FAILURE':
            b['failures'] += 1
        if is_suspicious:
            b['suspicions'] += 1
        if is_blocked:
            b['blocks'] += 1

        # record in live-feed
        self.records.appendleft(record)

        # append to logs.txt as JSON line
        with open(LOGS_PATH, 'a') as lf:
            lf.write(json.dumps(record) + '\n')

        # if newly blocked, persist to blocklist.txt
        if is_blocked and ip not in self.blocked_ips:
            self.blocked_ips.add(ip)
            with open(BLOCKLIST_PATH, 'a') as bf:
                bf.write(ip + '\n')

        return record

    def get_stats(self):
        # prepare arrays for charting
        labels = [b['start'] for b in self.buckets]
        return {
            'labels': labels,
            'attempts': [b['attempts'] for b in self.buckets],
            'failures': [b['failures'] for b in self.buckets],
            'suspicions': [b['suspicions'] for b in self.buckets],
            'blocks': [b['blocks'] for b in self.buckets],
        }

    def get_recent(self, limit=50):
        # return the most recent `limit` records
        return list(self.records)[:limit]