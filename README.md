# Login Abuse Detection and Defense Tool

A **lightweight**, **real-time** login-abuse detection system built with Flask, designed to simulate login traffic, detect multiple attack patterns, block offenders, and visualize everything on a live dashboard.

---

## 🚀 Live Demo

https://login-abuse-tracker.onrender.com  
> *Free-tier spin-up may take 15–30 s.*

---

## 📖 Usage
1. Click Run Simulation on the dashboard to simulate real non-attacker traffic.

2. Choose your attack type (normal / bruteforce / geohop / credstuff). All attacks can run in parallel.

3. Monitor the live-updating charts, recent log feed, and blocklist.

---

## 🔍 Features

- **Brute-Force Detection**  
  Tracks repeated failed attempts from the **same user & geo** region and flags + blocks after configurable threshold.
- **Geo-Hop Detection**  
  Flags rapid location changes for the **same user** and escalates to block.
- **Credential-Stuffing Detection**  
  Detects many distinct user-ID failures from the **same IP** within a sliding window.
- **Blocklist Enforcement**  
  Blocks by IP or by user (depending on attack type); persists across requests.
- **Attack Simulation Scripts**  
  - **Normal**: randomized IPs, users, geos, success/failure. Mimics real traffic.
  - **Brute-Force**: parallel workers hammer one user/geo with failures.  
  - **Geo-Hop**: one user hopping geos.  
  - **Cred-Stuff**: one IP cycling through unique users.
- **Real-Time Dashboard**  
  Live charts (Chart.js) of attempts, failures, suspicions, blocks; recent log feed; blocked list.
- **Stateless Reset**  
  Each simulation run clears logs, stats, and blocklist for a fresh start.

---

## ⚙️ Tech Stack

- **Backend**: Python 3.9+, Flask, `threading`, `collections.deque`  
- **Frontend**: HTML, Bootstrap, Chart.js, Fetch API  
- **Simulator**: `requests` library, configurable via REST endpoint  
- **Hosting**: Render (free-tier)  
- **Storage**: flat files (`logs.txt`, `blocklist.txt`)
