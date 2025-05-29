import random
import time
import argparse
import requests
import threading

# simulation parameters
GEO_REGIONS = ['US:NY', 'US:CA', 'US:TX', 'US:IL', 'US:FL',
               'GB:LN', 'GB:MN', 'GB:ED', 'FR:PA', 'FR:LY',
               'FR:MR', 'DE:BE', 'DE:DB', 'DE:MU', 'JP:TK',
               'JP:OS', 'JP:KY', 'CA:ON', 'CA:BC', 'CA:QC',
               'AU:NS', 'AU:VI', 'IN:DL', 'IN:MH', 'BR:SP']
USER_IDS = list(range(1, 999))
# default server endpoint
DEFAULT_URL = 'http://localhost:5000'

# -- User deck for draw without replacement --
class UserDeck:
    def __init__(self, user_ids):
        self.original = list(user_ids)
        self._reset_deck()

    def _reset_deck(self):
        self.deck = self.original.copy()
        random.shuffle(self.deck)

    def draw(self):
        if not self.deck:
            self._reset_deck()
        return self.deck.pop()

# single shared deck instance for all sims
deck = UserDeck(USER_IDS)

# dispatcher
def run_simulation(sim_type='normal', rate=2, duration=120, failure_rate=0.2, server_url=DEFAULT_URL):
    if sim_type == 'normal':
        return run_normal(rate, duration, failure_rate, server_url)
    elif sim_type == 'bruteforce':
        return run_bruteforce(rate, duration, failure_rate, server_url)
    elif sim_type == 'geohop':
        return run_geohop(rate, duration, failure_rate, server_url)
    elif sim_type == 'credstuff':
        return run_credstuff(rate, duration, failure_rate, server_url)

# Normal simulation using deck.draw()
def run_normal(rate, duration, failure_rate, server_url=DEFAULT_URL):
    end_time = time.time() + duration
    while time.time() < end_time:
        ip = f"192.168.0.{random.randint(1,999)}"
        # draw a unique user
        user_id = deck.draw()
        geo = random.choice(GEO_REGIONS)
        current_failure = random.uniform(0.1, 0.4)
        success = random.random() > current_failure
        payload = {
            'ip': ip,
            'user': user_id,
            'geo': geo,
            'sim_type': 'normal',
            'success': success
        }
        try:
            requests.post(f"{server_url}/attempt", json=payload)
        except Exception as e:
            print(f"Simulation error: {e}")
        time.sleep(random.uniform(0.1, 0.7))

# Bruteforce worker unchanged, draws user via deck
def bruteforce_worker(ip, user_id, geo, duration, server_url):
    """
    ip, user_id, geo, duration all as before,
    server_url is the full "http://host:port" you passed in.
    """
    end_time = time.time() + duration
    while time.time() < end_time:
        payload = {
            'ip':      ip,
            'user':    user_id,
            'geo':     geo,
            'sim_type':'bruteforce',
            'success': False
        }
        try:
            # <— use the passed-in server_url instead of the hard-coded one
            requests.post(f"{server_url}/attempt", json=payload)
        except Exception as e:
            print(f"[bruteforce worker] Error: {e}")

# Brute-force spawns threads, draws unique user

def run_bruteforce(rate, duration, failure_rate, server_url):
    user_id = random.choice(USER_IDS)
    geo     = random.choice(GEO_REGIONS)
    num_workers = 5
    threads = []
    for _ in range(num_workers):
        ip = f"192.168.0.{random.randint(1,254)}"
        t = threading.Thread(
            target=bruteforce_worker,
            args=(ip, user_id, geo, duration, server_url),  # <— correct
            daemon=True
        )
        t.start()
        threads.append(t)
    for t in threads:
        t.join()


# Geo-hop draws as before

def run_geohop(rate, duration, failure_rate, server_url=DEFAULT_URL):
    end_time = time.time() + duration
    user_id = deck.draw()
    prev_geo = random.choice(GEO_REGIONS)
    while time.time() < end_time:
        ip = f"192.168.0.{random.randint(1, 254)}"
        geo = random.choice(GEO_REGIONS)
        while geo == prev_geo:
            geo = random.choice(GEO_REGIONS)
        payload = {
            'ip': ip,
            'user': user_id,
            'geo': geo,
            'sim_type': 'geohop',
            'success': True
        }
        prev_geo = geo
        try:
            requests.post(f"{server_url}/attempt", json=payload)
        except Exception as e:
            print(f"[geohop] Error: {e}")
        time.sleep(random.uniform(1,5))

# Credential stuffing draws user for each attempt but ensures unique draws too
def run_credstuff(rate, duration, failure_rate, server_url=DEFAULT_URL):
    import random, time, requests
    # draw-without-replacement deck
    local_deck = UserDeck(USER_IDS)

    interval = 1.0 / rate
    end_time = time.time() + duration
    geo = random.choice(GEO_REGIONS)
    current_failure = random.uniform(0.1, 0.4)
    success = random.random() > current_failure
    ip = f"192.168.0.{random.randint(1,254)}"

    while time.time() < end_time:
        user_id = local_deck.draw()
        payload = {
            'ip':      ip,
            'user':    user_id,
            'geo':     geo,
            'sim_type':'credstuff',
            'success': success
        }
        try:
            requests.post(f"{server_url}/attempt", json=payload)
        except Exception as e:
            print(f"[credstuff] Error: {e}")
        time.sleep(random.uniform(1, 5))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simulate login traffic')
    parser.add_argument( '--type', default='normal', choices=['normal', 'bruteforce', 'geohop', 'credstuff'], help='Type of simulation to run')
    parser.add_argument( '--rate', type=float, default=2, help='Attempts per second')
    parser.add_argument( '--duration', type=int, default=30, help='Duration in seconds')
    parser.add_argument( '--failure-rate', type=float, default=0.2, help='Base failure probability')
    parser.add_argument( '--server-url', default=DEFAULT_URL, help='Flask server endpoint')
    args = parser.parse_args()

    print(f"Starting {args.type} simulation @ {args.server_url}: {args.rate} rps for {args.duration}s")

    run_simulation(sim_type=args.type, rate=args.rate, duration=args.duration, failure_rate=args.failure_rate, server_url=args.server_url)
