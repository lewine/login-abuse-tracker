import random
import time
import argparse
import requests

# simulation parameters
GEO_REGIONS = ['US:CA', 'US:NY', 'GB:LN', 'FR:PA', 'DE:BE']
USER_IDS = list(range(1, 11))

def run_simulation(sim_type='normal', rate=2, duration=120, failure_rate=0.2, server_url='http://localhost:5000'):
    end_time = time.time() + duration
    while time.time() < end_time:
        ip = f"192.168.0.{random.randint(1,254)}"
        user_id = random.choice(USER_IDS)
        geo = random.choice(GEO_REGIONS)
        current_failure = random.uniform(0.1, 0.4)
        success = random.random() > current_failure
        payload = {
            'ip': ip,
            'user': user_id,
            'geo': geo,
            'sim_type': sim_type,
            'success': success
        }
        try:
            requests.post(f"{server_url}/attempt", json=payload)
        except Exception as e:
            print(f"Simulation error: {e}")
        time.sleep(random.uniform(0.1, 0.7))
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simulate login traffic')
    parser.add_argument('--type', default='normal', choices=['normal','bruteforce','geohop','credstuff'])
    parser.add_argument('--rate', type=float, default=10, help='Attempts per second')
    parser.add_argument('--duration', type=int, default=30, help='Duration in seconds')
    parser.add_argument('--failure-rate', type=float, default=0.2, help='Base failure probability')
    parser.add_argument('--server-url', default='http://localhost:5000', help='Flask server endpoint')
    args = parser.parse_args()
    print(f"Starting {args.type} simulation @ {args.server_url}: {args.rate} rps for {args.duration}s")
    run_simulation(args.type, args.rate, args.duration, args.failure_rate, args.server_url)