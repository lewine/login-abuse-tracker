import random
import time
import argparse
import requests
import threading

# ──────────────────────────────────────────────────────────────────────────────
# Simulation parameters (static lists)
# ──────────────────────────────────────────────────────────────────────────────

GEO_REGIONS = [
    "US:NY", "US:CA", "US:TX", "US:IL", "US:FL",
    "GB:LN", "GB:MN", "GB:ED",
    "FR:PA", "FR:LY", "FR:MR",
    "DE:BE", "DE:DB", "DE:MU",
    "JP:TK", "JP:OS", "JP:KY",
    "CA:ON", "CA:BC", "CA:QC",
    "AU:NS", "AU:VI",
    "IN:DL", "IN:MH",
    "BR:SP"
]

USER_IDS = list(range(1, 1000))
DEFAULT_URL = "http://localhost:5000"


# ──────────────────────────────────────────────────────────────────────────────
# User‐deck class (draw without replacement)
# ──────────────────────────────────────────────────────────────────────────────

class UserDeck:
    """
    Maintains a shuffled deck of user IDs to draw without replacement.
    When the deck empties, it reshuffles automatically.
    """
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


# A single shared deck so that all simulations re‐use the same pool of user IDs.
deck = UserDeck(USER_IDS)


# ──────────────────────────────────────────────────────────────────────────────
# Dispatcher
# ──────────────────────────────────────────────────────────────────────────────

def run_simulation(sim_type, delay, iterations, failure_rate, server_url, workers=1):
    """
    Dispatch to the appropriate simulation function based on sim_type.
    - sim_type:     "normal" | "bruteforce" | "geohop" | "credstuff"
    - delay:        pause (in seconds) between each request
    - iterations:   number of requests each worker sends
    - failure_rate: probability (0.0–1.0) of marking an attempt as failure
    - server_url:   base Flask endpoint, e.g. "http://localhost:5000"
    - workers:      number of parallel threads to spawn (default=1)
    """
    if sim_type == "normal":
        return run_normal(delay, iterations, failure_rate, server_url, workers)
    elif sim_type == "bruteforce":
        return run_bruteforce(delay, iterations, failure_rate, server_url, workers)
    elif sim_type == "geohop":
        return run_geohop(delay, iterations, failure_rate, server_url, workers)
    elif sim_type == "credstuff":
        return run_credstuff(delay, iterations, failure_rate, server_url, workers)
    else:
        # Fallback: treat unknown type as a short normal sim
        return run_normal(delay, iterations, failure_rate, server_url, workers)


# ──────────────────────────────────────────────────────────────────────────────
# 1) Normal traffic simulation (possibly multi‐worker)
# ──────────────────────────────────────────────────────────────────────────────

def normal_worker(delay, iterations, failure_rate, server_url):
    """
    A single worker that sends `iterations` normal login attempts:
      - Each attempt: draw a unique user, pick a random geo
      - Each attempt has `failure_rate` chance of being marked failure
      - Sleeps `delay` seconds between each POST
    """
    for _ in range(iterations):
        ip = f"192.168.0.{random.randint(1, 999)}"
        user_id = deck.draw()
        geo = random.choice(GEO_REGIONS)

        # Decide success/failure based on failure_rate
        success = (random.random() > failure_rate)

        payload = {
            "ip":       ip,
            "user":     user_id,
            "geo":      geo,
            "sim_type": "normal",
            "success":  success
        }
        try:
            requests.post(f"{server_url}/attempt", json=payload)
        except Exception as e:
            print(f"[normal_worker] Error posting attempt: {e}")

        time.sleep(delay)


def run_normal(delay, iterations, failure_rate, server_url, workers=1):
    """
    Spawn `workers` threads, each running `normal_worker`:
      - Each worker sends approximately `iterations // workers` requests.
      - If `iterations` is not divisible by `workers`, the first few
        workers get an extra request to total exactly `iterations`.
    """
    # Divide iterations evenly
    base_iters = iterations // workers
    extra = iterations % workers
    threads = []

    for w in range(workers):
        this_count = base_iters + (1 if w < extra else 0)
        t = threading.Thread(
            target=normal_worker,
            args=(delay, this_count, failure_rate, server_url),
            daemon=True
        )
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


# ──────────────────────────────────────────────────────────────────────────────
# 2) Brute‐force attack simulation (multi‐worker)
# ──────────────────────────────────────────────────────────────────────────────

def bruteforce_worker(ip, user_id, geo, iterations, server_url, delay):
    """
    A single worker thread for brute‐force:
      - Sends `iterations` failed attempts for (ip,user_id,geo)
      - Sleeps `delay` seconds between each POST
    """
    for _ in range(iterations):
        payload = {
            "ip":       ip,
            "user":     user_id,
            "geo":      geo,
            "sim_type": "bruteforce",
            "success":  False
        }
        try:
            requests.post(f"{server_url}/attempt", json=payload)
        except Exception as e:
            print(f"[bruteforce_worker] Error: {e}")
        time.sleep(delay)


def run_bruteforce(delay, iterations, failure_rate, server_url, workers=5):
    """
    Spawn `workers` threads for brute‐force:
      - Choose one random user_id and one random geo
      - Each worker sends `iterations` failed attempts
      - Sleeps `delay` seconds between each attempt
    """
    user_id = random.choice(USER_IDS)
    geo = random.choice(GEO_REGIONS)
    threads = []

    for _ in range(workers):
        ip = f"192.168.0.{random.randint(1, 254)}"
        t = threading.Thread(
            target=bruteforce_worker,
            args=(ip, user_id, geo, iterations, server_url, delay),
            daemon=True
        )
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


# ──────────────────────────────────────────────────────────────────────────────
# 3) Geo‐hop attack simulation (multi‐worker)
# ──────────────────────────────────────────────────────────────────────────────

def geohop_worker(delay, iterations, server_url):
    """
    A single worker for geo‐hop:
      - Uses one unique user_id for all iterations
      - Each attempt switches to a new random geo (not equal to previous)
      - Each payload is marked success=True
      - Sleeps `delay` seconds between each attempt
    """
    user_id = deck.draw()
    prev_geo = random.choice(GEO_REGIONS)

    for _ in range(iterations):
        ip = f"192.168.0.{random.randint(1, 254)}"
        geo = random.choice(GEO_REGIONS)
        while geo == prev_geo:
            geo = random.choice(GEO_REGIONS)

        payload = {
            "ip":       ip,
            "user":     user_id,
            "geo":      geo,
            "sim_type": "geohop",
            "success":  True
        }
        prev_geo = geo

        try:
            requests.post(f"{server_url}/attempt", json=payload)
        except Exception as e:
            print(f"[geohop_worker] Error: {e}")

        time.sleep(delay)


def run_geohop(delay, iterations, failure_rate, server_url, workers=1):
    """
    Spawn `workers` threads for geo‐hop:
      - Each worker runs `iterations` attempts, switching geo each time
      - Sleeps `delay` seconds between attempts
    """
    threads = []
    for _ in range(workers):
        t = threading.Thread(
            target=geohop_worker,
            args=(delay, iterations, server_url),
            daemon=True
        )
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


# ──────────────────────────────────────────────────────────────────────────────
# 4) Credential‐stuffing attack simulation (multi‐worker)
# ──────────────────────────────────────────────────────────────────────────────

def credstuff_worker(delay, iterations, failure_rate, server_url):
    """
    A single worker for credential‐stuffing:
      - Uses one random IP and one random geo for all iterations
      - Each iteration: draw a new user_id, decide success/failure
      - Sleeps `delay` seconds between each attempt
    """
    local_deck = UserDeck(USER_IDS)
    geo = random.choice(GEO_REGIONS)
    ip = f"192.168.0.{random.randint(1, 254)}"

    for _ in range(iterations):
        user_id = local_deck.draw()
        current_failure = random.uniform(0.1, 0.4)
        success = (random.random() > current_failure)

        payload = {
            "ip":       ip,
            "user":     user_id,
            "geo":      geo,
            "sim_type": "credstuff",
            "success":  success
        }
        try:
            requests.post(f"{server_url}/attempt", json=payload)
        except Exception as e:
            print(f"[credstuff_worker] Error: {e}")

        time.sleep(delay)


def run_credstuff(delay, iterations, failure_rate, server_url, workers=1):
    """
    Spawn `workers` threads for credential‐stuffing:
      - Each worker sends `iterations` attempts from its own random IP
      - Sleeps `delay` seconds between each attempt
    """
    threads = []
    for _ in range(workers):
        t = threading.Thread(
            target=credstuff_worker,
            args=(delay, iterations, failure_rate, server_url),
            daemon=True
        )
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


# ──────────────────────────────────────────────────────────────────────────────
# Command‐line interface
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate login‐abuse traffic")
    parser.add_argument(
        "--type",
        default="normal",
        choices=["normal", "bruteforce", "geohop", "credstuff"],
        help="Type of simulation: normal | bruteforce | geohop | credstuff"
    )
    parser.add_argument(
        "--delay", type=float, default=1.0,
        help="Delay (seconds) between each request. E.g. 0.5 means 2 requests/sec."
    )
    parser.add_argument(
        "--iterations", type=int, default=30,
        help="Number of requests each worker sends."
    )
    parser.add_argument(
        "--failure-rate", type=float, default=0.2,
        help="Base failure probability (only used by normal & credstuff)"
    )
    parser.add_argument(
        "--workers", type=int, default=1,
        help="Number of parallel worker threads."
    )
    parser.add_argument(
        "--server-url", default=DEFAULT_URL,
        help="Flask server endpoint, e.g. http://localhost:5000"
    )
    args = parser.parse_args()

    print(
        f"Starting {args.type} simulation @ {args.server_url}:\n"
        f"  delay = {args.delay} sec between requests\n"
        f"  iterations = {args.iterations} requests per worker\n"
        f"  failure_rate = {args.failure_rate}\n"
        f"  workers = {args.workers}"
    )

    run_simulation(
        sim_type=args.type,
        delay=args.delay,
        iterations=args.iterations,
        failure_rate=args.failure_rate,
        server_url=args.server_url,
        workers=args.workers
    )
