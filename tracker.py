import os
import json
import time
from collections import deque, defaultdict

# Constants for bucketed stats
WINDOW_SIZE = 2    # seconds per bucket
MAX_BUCKETS = 5    # keep ~1 minute of history

# File paths
BLOCKLIST_PATH = os.path.join(os.getcwd(), "blocklist.txt")
LOGS_PATH = os.path.join(os.getcwd(), "logs.txt")


class AttackTracker:
    def __init__(self):
        # Detection thresholds (default values)
        self.brute_threshold = 5
        self.brute_window = 5
        self.geohop_threshold = 2
        self.cred_threshold = 2
        self.cred_window = 20

        # Clear logs and blocklist on startup
        open(LOGS_PATH, "w").close()
        open(BLOCKLIST_PATH, "w").close()
        self.blocked_ips = set()
        self.blocked_users = set()
        self.suspicious_ips = set()
        self.suspicious_users = set()

        # State for detection
        # Track recent failures per (user, geo)
        self.user_geo_failures = defaultdict(deque)
        # Track recent geos per user (for geo-hop detection), sized by geohop_threshold
        self.user_hops = defaultdict(lambda: deque(maxlen=self.geohop_threshold))
        # Remember last geo for each user
        self.user_last_geo = {}
        # Track recent (user, timestamp) pairs per (ip, geo) for credential stuffing
        self.ip_user_hits = defaultdict(deque)

        # Live-feed and time-series buckets
        self.records = deque(maxlen=1000)
        self.buckets = deque(maxlen=MAX_BUCKETS)
        self._start_new_bucket()

    def get_thresholds(self):
        """
        Return the current defense thresholds as a JSON-serializable dict.
        """
        return {
            "brute_threshold": self.brute_threshold,
            "brute_window": self.brute_window,
            "geohop_threshold": self.geohop_threshold,
            "cred_threshold": self.cred_threshold,
            "cred_window": self.cred_window,
        }

    def update_thresholds(self, **kwargs):
        """
        Update any provided thresholds. For example:
          { "brute_threshold": 7, "cred_window": 30 }
        """
        if "brute_threshold" in kwargs:
            self.brute_threshold = kwargs["brute_threshold"]
        if "brute_window" in kwargs:
            self.brute_window = kwargs["brute_window"]
        if "geohop_threshold" in kwargs:
            self.geohop_threshold = kwargs["geohop_threshold"]
        if "cred_threshold" in kwargs:
            self.cred_threshold = kwargs["cred_threshold"]
        if "cred_window" in kwargs:
            self.cred_window = kwargs["cred_window"]

        # After changing thresholds, we should resize any existing deques accordingly:
        # Rebuild user_hops to use the new geohop_threshold
        new_user_hops = defaultdict(lambda: deque(maxlen=self.geohop_threshold))
        for user, dq in self.user_hops.items():
            # Copy over existing geos (capped to new maxlen)
            for g in dq:
                new_user_hops[user].append(g)
        self.user_hops = new_user_hops

        # Rebuild any other sliding windows if necessary (not strictly required here)

    def _start_new_bucket(self):
        """
        Create a new time bucket for tracking attempts/failures/suspicions/blocks.
        Each bucket covers WINDOW_SIZE seconds.
        """
        start_ts = int(time.time() // WINDOW_SIZE) * WINDOW_SIZE
        bucket = {
            "start": start_ts,
            "attempts": 0,
            "failures": 0,
            "suspicions": 0,
            "blocks": 0,
        }
        self.buckets.append(bucket)
        self.current_bucket = bucket

    def _roll_buckets(self):
        """
        If enough time has passed, start a fresh bucket.
        """
        now = time.time()
        bucket_ts = int(now // WINDOW_SIZE) * WINDOW_SIZE
        if bucket_ts != self.current_bucket["start"]:
            self._start_new_bucket()

    def record_attempt(self, ip, user_id, geo, sim_type, result):
        """
        Called for each login attempt. Returns a dict with:
          { timestamp, ip, user, geo, sim_type, result,
            is_suspicious, is_blocked }
        """

        now = time.time()
        is_suspicious = False
        is_blocked = False

        # 1) Brute-force detection (count recent failures per (user, geo))
        if result == "FAILURE":
            key = (user_id, geo)
            dq = self.user_geo_failures[key]
            dq.append(now)

            # Prune any entries older than brute_window seconds
            while dq and dq[0] < now - self.brute_window:
                dq.popleft()

            # Clean up empty deques
            if not dq:
                del self.user_geo_failures[key]

            # If the number of failures in window reaches threshold, mark suspicious
            if len(dq) >= self.brute_threshold:
                is_suspicious = True

        # 2) Geo-hop detection (rapid geo changes per user)
        last_geo = self.user_last_geo.get(user_id)
        geo_hop_trigger = False
        if last_geo is None or geo != last_geo:
            hops = self.user_hops[user_id]
            hops.append(geo)

            # If the number of distinct geo hops reaches threshold, mark suspicious
            if len(hops) >= self.geohop_threshold:
                is_suspicious = True
                geo_hop_trigger = True

        # Update last known geo for this user
        self.user_last_geo[user_id] = geo

        # 3) Credential-stuffing detection (distinct users per (ip, geo))
        key2 = (ip, geo)
        dq2 = self.ip_user_hits.get(key2)
        if dq2 is None:
            dq2 = deque()
            self.ip_user_hits[key2] = dq2
        dq2.append((user_id, now))

        # Remove any hits older than cred_window seconds
        while dq2 and dq2[0][1] < now - self.cred_window:
            dq2.popleft()

        unique_users = {uid for uid, ts in dq2}
        if len(unique_users) >= self.cred_threshold:
            is_suspicious = True

        # 4) Escalation to block if a second suspicious strike arrives
        if is_suspicious:
            if geo_hop_trigger:
                # GeoHop: if user was already flagged suspicious, now block
                if str(user_id) in self.suspicious_users:
                    is_blocked = True
                    self.blocked_users.add(str(user_id))
                else:
                    self.suspicious_users.add(str(user_id))
            else:
                # BruteForce or CredStuff: use IP‐based suspicious set
                if ip in self.suspicious_ips:
                    is_blocked = True
                    self.blocked_users.add(str(user_id))
                else:
                    self.suspicious_ips.add(ip)

        # 5) If IP or user was already blocked previously, override to block
        if ip in self.blocked_ips or str(user_id) in self.blocked_users:
            is_blocked = True
            is_suspicious = True

        # 6) Roll buckets and tally counts into current bucket
        self._roll_buckets()
        b = self.current_bucket
        b["attempts"] += 1
        if result == "FAILURE":
            b["failures"] += 1
        if is_suspicious:
            b["suspicions"] += 1
        if is_blocked:
            b["blocks"] += 1

        # 7) Build the record for live feed
        rec = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "ip": ip,
            "user": user_id,
            "geo": geo,
            "sim_type": sim_type,
            "result": result,
            "is_suspicious": is_suspicious,
            "is_blocked": is_blocked,
        }

        # 8) Prepend to the live-feed deque
        self.records.appendleft(rec)

        # 9) Append to logs.txt
        with open(LOGS_PATH, "a") as lf:
            lf.write(json.dumps(rec) + "\n")

        return rec

    def get_stats(self):
        """
        Return a snapshot of the last MAX_BUCKETS buckets for charting:
          {
            labels:     [ timestamp1, timestamp2, … ],
            attempts:   [ count1, count2, … ],
            failures:   [ count1, count2, … ],
            suspicions: [ count1, count2, … ],
            blocks:     [ count1, count2, … ]
          }
        """
        labels = [b["start"] for b in self.buckets]
        return {
            "labels": labels,
            "attempts": [b["attempts"] for b in self.buckets],
            "failures": [b["failures"] for b in self.buckets],
            "suspicions": [b["suspicions"] for b in self.buckets],
            "blocks": [b["blocks"] for b in self.buckets],
        }

    def get_recent(self, limit=50):
        """
        Return up to `limit` of the most recent records (for the live‐feed box).
        """
        return list(self.records)[:limit]
