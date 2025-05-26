import requests
import random
import time

URL = "https://login-abuse-tracker.onrender.com/attempt"
test_ips = [f"192.168.0.{i}" for i in range(1, 6)]

# Clear logs and blocklist before simulating
for file in ["logs.txt", "blocklist.txt"]:
    with open(file, "w") as f:
        pass
print("[SIMULATE INIT] logs.txt and blocklist.txt cleared.")


def simulate():
    while True:
        ip = random.choice(test_ips)
        # Force IP 192.168.0.1 to fail more often
        if ip == "192.168.0.1":
            success = False if random.random() < 0.9 else True
        else:
            success = random.random() > 0.5

        response = requests.post(URL, json={"ip": ip, "success": success})
        print(response.json())
        time.sleep(random.uniform(0.1, 2.5))

if __name__ == "__main__":
    simulate()
