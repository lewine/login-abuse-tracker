// You can override the API base URL by setting VITE_API_URL in your .env (e.g. "http://localhost:5000").
// Otherwise it defaults to localhost:5000.
const BASE_URL = import.meta.env.VITE_API_URL ?? "";
//VITE_API_URL=https://your-deployed-backend.com

// Helper: check response, parse JSON, or throw.
async function checkRes(res) {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

/**
 * Fetch the current stats object from Flask:
 *  
 * Expected JSON shape (example):
 * {
 *   attempts:   [0, 1, 2, ...],   // arrays of counts over time
 *   failures:   [0, 0, 1, ...],
 *   suspicions: [0, 0, 1, ...],
 *   blocks:     [0, 0, 0, ...],
 *   labels:     [1677771234, 1677771235, ...],  // Unix timestamps for X-axis
 *   recent: [
 *     {
 *       timestamp: 1677771235,
 *       ip: "1.2.3.4",
 *       geo: "US",
 *       user: "alice",
 *       sim_type: "bruteforce",
 *       result: "FAILURE",
 *       is_suspicious: true,
 *       is_blocked: false
 *     },
 *     ...
 *   ]
 * }
 */
export async function getStats() {
  const res = await fetch(`${BASE_URL}/stats`);
  return checkRes(res);
}

/**
 * POST /simulate with { sim_type: "normal" | "bruteforce" | "geohop" | "credstuff" }
 * Returns { status: "ok" } (if everything went through).
 */
export async function simulate(
  simType,
  delay = 1.0,
  iterations = 30,
  failureRate = 0.2,
  workers = 1
) {
  const payload = {
    sim_type: simType,
    delay: delay,
    iterations: iterations,
    failure_rate: failureRate,
    workers: workers,
  };

  const res = await fetch(`${BASE_URL}/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return checkRes(res);
}

/**
 * GET /thresholds { bruteforce_limit: number, geohop_interval: number, credstuff_limit: number }
 */
export async function getThresholds() {
  const res = await fetch(`${BASE_URL}/thresholds`);
  return checkRes(res);
}

/**
 * POST /thresholds
 * Accepts { bruteforce_limit: number, geohop_interval: number, credstuff_limit: number }
 * Returns { status: "thresholds updated" } (or similar).
 */
export async function setThresholds(thresholdsObj) {
  const res = await fetch(`${BASE_URL}/thresholds`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(thresholdsObj),
  });
  return checkRes(res);
}

export async function reset() {
  const res = await fetch(`${BASE_URL}/reset`, {
    method: "POST",
  });
  return checkRes(res);
}

/**
 * GET /blocklist
 * Returns an array of { type: "IP"|"USER", value: string }
 */

export async function getBlocklist() {
  const res = await fetch(`${BASE_URL}/blocklist`);
  return checkRes(res);
}
