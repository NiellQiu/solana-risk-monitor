const stateLabel = document.getElementById("stateLabel");
const riskTable = document.getElementById("riskTable");
const gainTable = document.getElementById("gainTable");
const signalTable = document.getElementById("signalTable");
const feed = document.getElementById("feed");

document.getElementById("startBtn").addEventListener("click", () => post("/api/monitor/start"));
document.getElementById("stopBtn").addEventListener("click", () => post("/api/monitor/stop"));
document.getElementById("refreshBtn").addEventListener("click", refreshAll);

async function post(url) {
  await fetch(url, { method: "POST" });
  await refreshState();
}

async function refreshState() {
  const state = await fetchJson("/api/monitor/state");
  stateLabel.textContent = `Running: ${state.running} | Poll: ${state.poll_interval_seconds}s | Tracked: ${state.tracked_tokens}`;
}

async function refreshRisk() {
  const rows = await fetchJson("/api/risk/top");
  riskTable.innerHTML = "<tr><th>Symbol</th><th>Score</th><th>Risk</th><th>Reason</th></tr>" +
    rows.map((r) => `<tr><td>${r.symbol}</td><td>${r.score}</td><td>${r.risk_level}</td><td>${(r.reasons || [])[0] || ""}</td></tr>`).join("");
}

async function refreshGain() {
  const rows = await fetchJson("/api/gain/top");
  gainTable.innerHTML = "<tr><th>Symbol</th><th>EV %</th><th>Upside %</th><th>Downside %</th><th>Conf</th></tr>" +
    rows.map((r) => `<tr><td>${r.symbol}</td><td>${r.expected_value_pct}</td><td>${r.estimated_upside_pct}</td><td>${r.estimated_downside_pct}</td><td>${r.confidence}</td></tr>`).join("");
}

async function refreshSignals() {
  const rows = await fetchJson("/api/signals/unified");
  signalTable.innerHTML = "<tr><th>Source</th><th>Name</th><th>Score</th><th>Risk</th><th>Summary</th></tr>" +
    rows.map((r) => `<tr><td>${r.source}</td><td>${r.name}</td><td>${r.score}</td><td>${r.risk_level}</td><td>${r.summary}</td></tr>`).join("");
}

async function refreshAll() {
  await Promise.all([refreshState(), refreshRisk(), refreshGain(), refreshSignals()]);
}

async function fetchJson(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Request failed: ${url}`);
  return res.json();
}

const source = new EventSource("/api/stream");
source.onmessage = (event) => {
  const payload = JSON.parse(event.data);
  const lines = (payload.events || []).map((e) => `${e.time} | ${e.kind} | ${e.symbol || ""} ${e.score || ""} ${e.risk || ""} EV:${e.ev_pct || ""}`);
  feed.textContent = lines.join("\n");
  refreshState();
};

refreshAll();
