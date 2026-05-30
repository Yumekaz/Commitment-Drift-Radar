let allRows = [];
let health = {};

async function loadHealth() {
  const res = await fetch("/api/health");
  const data = await res.json();
  health = data;
  const pill = document.getElementById("mode-pill");
  pill.textContent = data.coral_live ? "LIVE CORAL MODE" : "DEMO MODE";
  document.getElementById("health-title").textContent = data.coral_live
    ? "Live Coral query path"
    : "Demo data path";
  document.getElementById("health-detail").textContent = data.coral_live
    ? "Backend is executing Coral SQL."
    : "Local CSVs simulate the joined Coral result for credential-free review.";
  document.getElementById("coral-command").textContent = data.coral_command;
  document.getElementById("source-list").innerHTML = (data.sources || [])
    .map(source => `<span>${escapeHtml(source)}</span>`)
    .join("");
}

async function loadRisks() {
  const res = await fetch("/api/risks");
  const data = await res.json();
  if (data.error) {
    document.getElementById("riskRows").innerHTML =
      `<tr><td colspan="8">${escapeHtml(data.error)}</td></tr>`;
    return;
  }
  allRows = data.rows || [];
  renderMetrics(allRows);
  renderRows();
}

function renderMetrics(rows) {
  const totalRevenue = rows.reduce((sum, row) => sum + Number(row.paid_last_90_days || 0), 0);
  document.getElementById("metric-total").textContent = String(rows.length);
  document.getElementById("metric-critical").textContent =
    String(rows.filter(row => row.risk_level === "CRITICAL").length);
  document.getElementById("metric-high").textContent =
    String(rows.filter(row => row.risk_level === "HIGH").length);
  document.getElementById("metric-revenue").textContent = `$${Math.round(totalRevenue).toLocaleString()}`;
}

function renderRows() {
  const term = document.getElementById("search").value.toLowerCase();
  const filter = document.getElementById("riskFilter").value;
  const rows = allRows.filter(row => {
    const blob = JSON.stringify(row).toLowerCase();
    return (!filter || row.risk_level === filter) && (!term || blob.includes(term));
  });

  const body = document.getElementById("riskRows");
  if (!rows.length) {
    body.innerHTML = `<tr><td colspan="8">No commitments match the current filters.</td></tr>`;
    return;
  }

  body.innerHTML = rows.map(row => `
    <tr data-feature-key="${escapeAttr(row.feature_key)}" tabindex="0">
      <td><span class="badge ${row.risk_level}">${row.risk_level} / ${row.risk_score}</span></td>
      <td>${escapeHtml(row.customer_name)}</td>
      <td>${escapeHtml(row.feature_name)}</td>
      <td>${escapeHtml(row.promised_date)}</td>
      <td>${escapeHtml(row.engineering_status || "unknown")}</td>
      <td>${escapeHtml(String(row.open_tickets || 0))}</td>
      <td>$${Number(row.paid_last_90_days || 0).toLocaleString()}</td>
      <td>${String(row.rollout_enabled).toLowerCase() === "true" ? "Enabled" : "Not enabled"}</td>
    </tr>
  `).join("");

  body.querySelectorAll("tr[data-feature-key]").forEach(rowEl => {
    rowEl.addEventListener("click", () => loadEvidence(rowEl.dataset.featureKey));
    rowEl.addEventListener("keydown", event => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        loadEvidence(rowEl.dataset.featureKey);
      }
    });
  });
}

async function loadEvidence(featureKey) {
  const res = await fetch(`/api/evidence/${encodeURIComponent(featureKey)}`);
  const data = await res.json();
  if (data.error) {
    document.getElementById("evidence").textContent = data.error;
    return;
  }

  const row = data.row;
  const exp = data.explanation;
  document.getElementById("evidence").innerHTML = `
    <h3>${escapeHtml(exp.summary)}</h3>
    <div class="action-box">
      <span>Recommended action</span>
      <strong>${escapeHtml(exp.recommended_action)}</strong>
    </div>
    <h4>Why this is risky</h4>
    <ul class="reason-list">
      ${exp.reasons.map(r => `<li>${escapeHtml(r)}</li>`).join("")}
    </ul>
    <h4>Source evidence</h4>
    <div class="evidence-grid">
      <div><span>Customer promise</span><strong>${escapeHtml(row.promised_date || "No date")}</strong></div>
      <div><span>Linear/Jira</span><strong>${escapeHtml(row.linear_issue_key || "Missing")} / ${escapeHtml(row.engineering_status || "unknown")}</strong></div>
      <div><span>GitHub</span><strong>${row.pr_url ? `<a href="${escapeAttr(row.pr_url)}" target="_blank" rel="noreferrer">Merged PR</a>` : "No merged PR found"}</strong></div>
      <div><span>Slack</span><strong>${escapeHtml(row.latest_blocker || "No blocker message")}</strong></div>
      <div><span>Intercom</span><strong>${escapeHtml(row.latest_support_subject || "No open support subject")}</strong></div>
      <div><span>Stripe</span><strong>$${Number(row.paid_last_90_days || 0).toLocaleString()}</strong></div>
      <div><span>LaunchDarkly</span><strong>${String(row.rollout_enabled).toLowerCase() === "true" ? "Enabled" : "Not enabled"}</strong></div>
      <div><span>Query path</span><strong>${escapeHtml(health.coral_command || "coral/queries/commitment_risk.sql")}</strong></div>
    </div>
  `;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
  }[c]));
}

function escapeAttr(value) {
  return escapeHtml(value).replace(/`/g, "&#096;");
}

document.getElementById("refresh").addEventListener("click", loadRisks);
document.getElementById("search").addEventListener("input", renderRows);
document.getElementById("riskFilter").addEventListener("change", renderRows);

loadHealth();
loadRisks();
