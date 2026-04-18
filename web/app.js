const stateLabel = document.getElementById("stateLabel");
const riskTable = document.getElementById("riskTable");
const gainTable = document.getElementById("gainTable");
const pickTable = document.getElementById("pickTable");
const reboundTable = document.getElementById("reboundTable");
const signalTable = document.getElementById("signalTable");
const feed = document.getElementById("feed");
const capitalModal = document.getElementById("capitalModal");
const depositInput = document.getElementById("depositInput");
const riskPctInput = document.getElementById("riskPctInput");
const minScoreInput = document.getElementById("minScoreInput");
const minRRInput = document.getElementById("minRRInput");
const profileSummary = document.getElementById("profileSummary");

const profile = {
  depositUsd: Number(localStorage.getItem("depositUsd") || 10),
  riskPct: Number(localStorage.getItem("riskPct") || 10),
  minScore: Number(localStorage.getItem("minScore") || 70),
  minRR: Number(localStorage.getItem("minRR") || 1.2),
};

document.getElementById("startBtn").addEventListener("click", () => post("/api/monitor/start"));
document.getElementById("stopBtn").addEventListener("click", () => post("/api/monitor/stop"));
document.getElementById("refreshBtn").addEventListener("click", refreshAll);
document.getElementById("capitalBtn").addEventListener("click", openModal);
document.getElementById("closeCapitalBtn").addEventListener("click", closeModal);
document.getElementById("saveCapitalBtn").addEventListener("click", saveProfileFromModal);

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
  gainTable.innerHTML = "<tr><th>Symbol</th><th>EV %</th><th>Upside %</th><th>Downside %</th><th>R:R</th><th>Conf</th></tr>" +
    rows.map((r) => `<tr><td>${r.symbol}</td><td>${r.expected_value_pct}</td><td>${r.estimated_upside_pct}</td><td>${r.estimated_downside_pct}</td><td>${r.risk_reward_ratio}</td><td>${r.confidence}</td></tr>`).join("");
}

async function refreshPicks() {
  const query = new URLSearchParams({
    min_score: String(profile.minScore),
    min_risk_reward: String(profile.minRR),
    limit: "20",
  });
  const rows = await fetchJson(`/api/picks/top?${query.toString()}`);
  const riskCapital = (profile.depositUsd * profile.riskPct) / 100;
  pickTable.innerHTML = "<tr><th>Symbol</th><th>Score</th><th>Risk</th><th>EV %</th><th>R:R</th><th>Position $</th><th>Projected +$</th><th>Projected -$</th><th>Conf</th><th>Summary</th></tr>" +
    rows.map((r) => {
      const projectedGain = ((r.estimated_upside_pct / 100) * riskCapital).toFixed(2);
      const projectedLoss = ((r.estimated_downside_pct / 100) * riskCapital).toFixed(2);
      return `<tr><td>${r.symbol}</td><td>${r.score}</td><td>${r.risk_level}</td><td>${r.expected_value_pct}</td><td>${r.risk_reward_ratio}</td><td>${riskCapital.toFixed(2)}</td><td>${projectedGain}</td><td>${projectedLoss}</td><td>${r.confidence}</td><td>${r.summary}</td></tr>`;
    }).join("");
}

async function refreshSignals() {
  const rows = await fetchJson("/api/signals/unified");
  signalTable.innerHTML = "<tr><th>Source</th><th>Name</th><th>Score</th><th>Risk</th><th>Summary</th></tr>" +
    rows.map((r) => `<tr><td>${r.source}</td><td>${r.name}</td><td>${r.score}</td><td>${r.risk_level}</td><td>${r.summary}</td></tr>`).join("");
}

async function refreshRebound() {
  const rows = await fetchJson("/api/rebound/top?limit=20");
  reboundTable.innerHTML =
    "<tr><th>Symbol</th><th>Status</th><th>Cycles</th><th>Score</th><th>MCap $</th><th>Drawdown %</th><th>Vol Recovery</th><th>EV %</th><th>R:R</th><th>Summary</th></tr>" +
    rows
      .map(
        (r) =>
          `<tr><td>${r.symbol}</td><td>${r.status}</td><td>${r.confirmation_cycles}</td><td>${r.score}</td><td>${r.market_cap_usd}</td><td>${r.drawdown_pct}</td><td>${r.volume_recovery_ratio}</td><td>${r.expected_value_pct}</td><td>${r.risk_reward_ratio}</td><td>${r.summary}</td></tr>`
      )
      .join("");
}

async function refreshAll() {
  await Promise.all([
    refreshState(),
    refreshRisk(),
    refreshGain(),
    refreshPicks(),
    refreshRebound(),
    refreshSignals(),
  ]);
  renderProfileSummary();
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

function renderProfileSummary() {
  profileSummary.textContent = `Deposit: $${profile.depositUsd.toFixed(2)} | Risk per pick: ${profile.riskPct}% | Size per pick: $${((profile.depositUsd * profile.riskPct)/100).toFixed(2)} | Min score: ${profile.minScore} | Min R:R: ${profile.minRR}`;
}

function loadProfileInputs() {
  depositInput.value = String(profile.depositUsd);
  riskPctInput.value = String(profile.riskPct);
  minScoreInput.value = String(profile.minScore);
  minRRInput.value = String(profile.minRR);
  document.getElementById("modalDeposit").value = String(profile.depositUsd);
  document.getElementById("modalRiskPct").value = String(profile.riskPct);
  document.getElementById("modalMinScore").value = String(profile.minScore);
  document.getElementById("modalMinRR").value = String(profile.minRR);
}

function openModal() {
  loadProfileInputs();
  capitalModal.style.display = "flex";
}

function closeModal() {
  capitalModal.style.display = "none";
}

function saveProfileFromModal() {
  profile.depositUsd = Math.max(1, Number(document.getElementById("modalDeposit").value || 10));
  profile.riskPct = Math.min(100, Math.max(1, Number(document.getElementById("modalRiskPct").value || 10)));
  profile.minScore = Math.min(100, Math.max(1, Number(document.getElementById("modalMinScore").value || 70)));
  profile.minRR = Math.max(0.1, Number(document.getElementById("modalMinRR").value || 1.2));
  localStorage.setItem("depositUsd", String(profile.depositUsd));
  localStorage.setItem("riskPct", String(profile.riskPct));
  localStorage.setItem("minScore", String(profile.minScore));
  localStorage.setItem("minRR", String(profile.minRR));
  loadProfileInputs();
  closeModal();
  refreshAll();
}

depositInput.addEventListener("change", () => {
  document.getElementById("modalDeposit").value = depositInput.value;
  saveProfileFromModal();
});
riskPctInput.addEventListener("change", () => {
  document.getElementById("modalRiskPct").value = riskPctInput.value;
  saveProfileFromModal();
});
minScoreInput.addEventListener("change", () => {
  document.getElementById("modalMinScore").value = minScoreInput.value;
  saveProfileFromModal();
});
minRRInput.addEventListener("change", () => {
  document.getElementById("modalMinRR").value = minRRInput.value;
  saveProfileFromModal();
});

loadProfileInputs();
refreshAll();
