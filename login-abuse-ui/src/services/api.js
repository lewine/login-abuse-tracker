const BASE_URL = import.meta.env.VITE_API_URL ?? "";

async function checkRes(res) {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}


export async function getStats() {
  const res = await fetch(`${BASE_URL}/stats`);
  return checkRes(res);
}

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


export async function getThresholds() {
  const res = await fetch(`${BASE_URL}/thresholds`);
  return checkRes(res);
}


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

export async function getBlocklist() {
  const res = await fetch(`${BASE_URL}/blocklist`);
  return checkRes(res);
}
