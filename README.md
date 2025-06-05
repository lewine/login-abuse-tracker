# Login Abuse Detection and Defense Tool

A **lightweight**, **real-time** login-abuse detection system built with Flask, designed to simulate login traffic, detect multiple attack patterns, block offenders, and visualize everything on a live dashboard.

## Live Demo
https://login-abuse-tracker-docker.onrender.com
![Dockerized](https://img.shields.io/badge/deployed%20with-docker-blue)

### Deployed with Docker  
This project is containerized and deployed via Docker on Render, using GitHub Actions for CI testing.

> *Free-tier spin-up may take 15–30 s.*

## Usage
1. Click Run Simulation on the dashboard to simulate real non-attacker traffic.

2. Choose your attack type (normal / bruteforce / geohop / credstuff). All attacks can run in parallel. There is a settings tab to adjust the defense detection and the attack simulations.

3. Monitor the live-updating charts, recent log feed, and blocklist.

## Features

- **Attack Simulation**  
  - **Normal**: random IPs, user IDs, geos, with a configurable base failure rate (mimics legitimate traffic).  
  - **Brute-Force**: multiple worker threads hammer a single user/geo combo with repeated failures.  
  - **Geo-Hop**: a single user leaps across different geolocations faster than the set threshold.  
  - **Credential-Stuffing**: one IP tries many unique users within a sliding window.  
  - All attack parameters (delay, iterations, failure rate, number of workers) are adjustable via the Settings panel.

- **Real-Time Detection & Defense**  
  - **Brute-Force**: tracks recent failures per (user, geo) in a sliding window → “suspicious” on threshold, “blocked” on second violation.  
  - **Geo-Hop**: tracks each user’s consecutive distinct geos → “suspicious” when they exceed a threshold count, “blocked” on second violation.  
  - **Credential-Stuffing**: tracks distinct user hits per (IP, geo) in a sliding window → “blocked” when the unique user count ≥ threshold.  
  - **Persistent Blocklist**: once an IP/user is blocked, they cannot submit further attempts; blocklist stored in `blocklist.txt`.

- **Dashboard (UI)**  
  - **Stats Cards**: immediate summary of “Suspicious,” “Recent Attempts,” “Failures,” “Blocks.”  
  - **Live Chart (Chart.js)**: time-bucketed graph of attempts/failures/suspicions/blocks (updated every second).  
  - **Recent Feed**: scrollable list of the 50 most recent login attempts—each line color-coded if suspicious or blocked.  
  - **Blocked Feed**: list of unique IPs/users currently blocked (pulled from `blocklist.txt`).  
  - **Settings Dropdown**: edit both “Defense Settings” (thresholds) and “Attack Settings” (delay, iterations, workers) in one unified panel.

- **Stateless Reset**  
  Hitting “Reset” clears:
  - `logs.txt` (live-feed persists only in memory but gets rewritten on reset)  
  - `blocklist.txt` (removes all persistent blocks)  
  - All in-memory counters & records → yields a brand-new fresh start.

## Tech Stack

- **Backend**: Python 3.9+, Flask, `threading`, `collections.deque`  
- **Frontend**: HTML, Bootstrap, Chart.js, Fetch API  
- **Simulator**: `requests` library, configurable via REST endpoint  
- **Hosting**: Render (free-tier)  
- **Storage**: flat files (`logs.txt`, `blocklist.txt`)
