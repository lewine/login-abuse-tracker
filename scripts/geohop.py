import random
import time
import argparse
import requests

# simulation parameters
GEO_REGIONS = ['US:CA', 'US:NY', 'GB:LN', 'FR:PA', 'DE:BE']
USER_IDS = list(range(1, 11))

# default server endpoint
DEFAULT_URL = 'http://localhost:5000'

def run_simulation(rate, duration, failure_rate, server_url='http://localhost:5000'):
    interval = 1.0 / rate
    end_time = time.time() + duration
    # choose one user and simulate geo hops
    user_id = random.choice(USER_IDS)
    prev_geo = random.choice(GEO_REGIONS)
    while time.time() < end_time:
        ip = f"192.168.0.{random.randint(1, 254)}"
        # pick a new geo different from previous
        geo = random.choice(GEO_REGIONS)
        while geo == prev_geo:
            geo = random.choice(GEO_REGIONS)
        #success = random.random() > failure_rate
        payload = {
            'ip': ip,
            'user': user_id,
            'geo': geo,
            'sim_type': 'geohop',
            'success': False
        }
        prev_geo = geo
        try:
            requests.post(f"{server_url}/attempt", json=payload)
        except Exception as e:
            print(f"[geohop] Error: {e}")
        time.sleep(interval)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simulate login traffic')
    parser.add_argument('--type', default='normal',
                        choices=['normal', 'bruteforce', 'geohop', 'credstuff'],
                        help='Type of simulation to run')
    parser.add_argument('--rate', type=float, default=2,
                        help='Attempts per second')
    parser.add_argument('--duration', type=int, default=30,
                        help='Duration in seconds')
    parser.add_argument('--failure-rate', type=float, default=0.2,
                        help='Base failure probability')
    parser.add_argument('--server-url', default=DEFAULT_URL,
                        help='Flask server endpoint')
    args = parser.parse_args()

    print(f"Starting {args.type} simulation @ {args.server_url}: {args.rate} rps for {args.duration}s")

