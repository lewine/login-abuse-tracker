# Login Abuse Tracker

A lightweight Flask-based login abuse tracker that detects brute-force login attempts, blocks malicious IPs, and presents a live visual dashboard of login activity.

---

## Live Demo: https://login-abuse-tracker.onrender.com

Dashboard: https://dashboard.render.com/web/srv-d0qevpmmcj7s73dvvo00/deploys/dep-d0qgaemmcj7s73e10nig

Wait 15–30 seconds if the page is inactive (free tier spins down).  
Once loaded, hit "Run Simulation" button to start simulating random login activity.

---

## Features

- **Brute-force detection** — blocks IPs after 3 failed login attempts
- **Blocklist enforcement** — ignores requests from blocked IPs
- **Real-time dashboard** — shows stats, charted login attempts, and blocklist
- **Flask API backend** — /attempt, /stats, /blocklist, /recent-logs
- **Frontend UI — HTML** + Chart.js dashboard
- **Simulator mode** — generates random traffic with skewed failure rates
- **State reset after each simulation** (stats, logs, and blocklist)

---

## Tech Stack

- **Backend:** Python, Flask
- **Frontend:** HTML + Chart.js
- **DevOps:** Render (Free Tier Hosting)
- **Other:** threading, requests, random, deque, file I/O

---

## How It Works

- The backend tracks IPs and maintains counters for failed attempts.
- On 3+ failures, the IP is blocklisted.
- Stats are updated and exposed via JSON API.
- The UI polls /stats, /blocklist, and /recent-logs every second.
- Simulated traffic is sent via run_simulation() when the dashboard loads.
