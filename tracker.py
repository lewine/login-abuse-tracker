import os
import json
import time
from collections import deque, defaultdict
from simulate_api import UserDeck, USER_IDS 

# constants
WINDOW_SIZE = 2   # seconds per bucket
MAX_BUCKETS = 5  # keep ~1 minute of history

# detection thresholds
BRUTE_THRESHOLD = 15        # failures to trigger brute force detection
BRUTE_WINDOW = 5          # seconds for brute force sliding window
GEOHOP_THRESHOLD = 2          # seconds for rapid geo-hop detection
CRED_THRESHOLD = 2         # distinct user hits to trigger credential stuffing detection
CRED_WINDOW = 15           # seconds for credential stuffing sliding window

# file paths
BLOCKLIST_PATH = os.path.join(os.getcwd(), 'blocklist.txt')
LOGS_PATH = os.path.join(os.getcwd(), 'logs.txt')

class AttackTracker:
    def __init__(self):
        # clear logs and blocklist on startup
        open(LOGS_PATH, 'w').close()
        open(BLOCKLIST_PATH, 'w').close()
        self.blocked_ips = set()
        self.blocked_users = set()
        self.suspicious_ips = set()
        self.suspicious_users = set()


        # state for detection
        self.user_geo_failures = defaultdict(deque)
        self.user_hops = defaultdict(lambda: deque(maxlen=GEOHOP_THRESHOLD))
        self.user_last_geo = {}
        self.ip_user_hits = defaultdict(deque)  # (user_id, timestamp) per IP

        # live-feed and time-series
        self.records = deque(maxlen=1000)
        self.buckets = deque(maxlen=MAX_BUCKETS)
        self._start_new_bucket()

    def _start_new_bucket(self):
        start_ts = int(time.time() // WINDOW_SIZE) * WINDOW_SIZE
        bucket = {'start': start_ts, 'attempts': 0, 'failures': 0,
                  'suspicions': 0, 'blocks': 0}
        self.buckets.append(bucket)
        self.current_bucket = bucket

    def _roll_buckets(self):
        now = time.time()
        bucket_ts = int(now // WINDOW_SIZE) * WINDOW_SIZE
        if bucket_ts != self.current_bucket['start']:
            self._start_new_bucket()

    def record_attempt(self, ip, user_id, geo, sim_type, result,
                       is_suspicious=False, is_blocked=False):
        now = time.time()
        # detection flags cleared; we'll set based on behavior
        is_suspicious = False
        is_blocked = False

        # 1) Brute-force detection: count recent failures per IP
        if result == 'FAILURE':
            key = (user_id, geo)
            dq = self.user_geo_failures[key]
            dq.append(now)

            # prune anything older than the sliding window
            while dq and dq[0] < now - BRUTE_WINDOW:
                dq.popleft()

            # clean up empty deques
            if not dq:
                del self.user_geo_failures[key]

            # only flag if this user→geo combo has hit the threshold
            if len(dq) >= BRUTE_THRESHOLD:
                is_suspicious = True

        # 2) Geo-hop detection: rapid geo change per user (ignore IP)
        last_geo = self.user_last_geo.get(user_id)
        geo_hop_trigger = False
        if last_geo is None or geo != last_geo:
            hops = self.user_hops[user_id]
            hops.append(geo)
            if len(hops) >= GEOHOP_THRESHOLD:
                is_suspicious = True
                geo_hop_trigger = True
        # update last geo
        self.user_last_geo[user_id] = geo

        # 3) Credential stuffing: distinct users per IP+Geo
        key2 = (ip, geo)
        dq2 = self.ip_user_hits.get(key2)
        if dq2 is None:
            dq2 = deque()
            self.ip_user_hits[key2] = dq2
        dq2.append((user_id, now))
        # remove old hits beyond window
        while dq2 and dq2[0][1] < now - CRED_WINDOW:
            dq2.popleft()
        unique_users = {uid for uid, ts in dq2}
        if len(unique_users) >= CRED_THRESHOLD:
            is_suspicious = True

        # escalation → block
        if is_suspicious:
            if geo_hop_trigger:
                # first geo-hop strike marks user suspicious
                if str(user_id) in self.suspicious_users:
                    # second geo-hop strike → block
                    is_blocked = True
                    self.blocked_users.add(str(user_id))
                else:
                    self.suspicious_users.add(str(user_id))
            else:
                # brute-force: second strike logic on IP
                if ip in self.suspicious_ips:
                    is_blocked = True
                    self.blocked_users.add(str(user_id))
                else:
                    self.suspicious_ips.add(ip)

        # persistent blocklist override
        if ip in self.blocked_ips or str(user_id) in self.blocked_users:
            is_blocked = True
            is_suspicious = True

        # roll buckets and tally
        self._roll_buckets()
        rec = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'ip': ip,
            'user': user_id,
            'geo': geo,
            'sim_type': sim_type,
            'result': result,
            'is_suspicious': is_suspicious,
            'is_blocked': is_blocked
        }
        b = self.current_bucket
        b['attempts'] += 1
        if result == 'FAILURE': b['failures'] += 1
        if is_suspicious:       b['suspicions'] += 1
        if is_blocked:          b['blocks'] += 1

        # record in live-feed
        self.records.appendleft(rec)
        # append to logs
        with open(LOGS_PATH, 'a') as lf:
            lf.write(json.dumps(rec) + '\n')
        
        return rec

    def get_stats(self):
        labels = [b['start'] for b in self.buckets]
        return {
            'labels': labels,
            'attempts': [b['attempts'] for b in self.buckets],
            'failures': [b['failures'] for b in self.buckets],
            'suspicions': [b['suspicions'] for b in self.buckets],
            'blocks': [b['blocks'] for b in self.buckets]
        }

    def get_recent(self, limit=50):
        return list(self.records)[:limit]
