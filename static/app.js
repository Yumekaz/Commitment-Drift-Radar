let allRows = [];

async function loadHealth() {
  const res = await fetch("/api/health");
  const data = await res.json();
  const pill = document.getElementById("mode-pill");
  pill.textContent = data.coral_live ? "LIVE CORAL MODE" : "DEMO MODE";
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
  renderRows();
}

function renderRows() {
  const term = document.getElementById("search").value.toLowerCase();
  const filter = document.getElementById("riskFilter").value;
  const rows = allRows.filter(row => {
    const blob = JSON.stringify(row).toLowerCase();
    return (!filter || row.risk_level === filter) && (!term || blob.includes(term));
  });

  document.getElementById("riskRows").innerHTML = rows.map(row => `
    <tr onclick="loadEvidence('${escapeAttr(row.feature_key)}')">
      <td><span class="badge ${row.risk_level}">${row.risk_level} · ${row.risk_score}</span></td>
      <td>${escapeHtml(row.customer_name)}</td>
      <td>${escapeHtml(row.feature_name)}</td>
      <td>${escapeHtml(row.promised_date)}</td>
      <td>${escapeHtml(row.engineering_status || "unknown")}</td>
      <td>${escapeHtml(String(row.open_tickets || 0))}</td>
      <td>$${Number(row.paid_last_90_days || 0).toLocaleString()}</td>
      <td>${String(row.rollout_enabled).toLowerCase() === "true" ? "Enabled" : "Not enabled"}</td>
    </tr>
  `).join("");
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
    <p><strong>Recommended action:</strong> ${escapeHtml(exp.recommended_action)}</p>
    <h4>Joined evidence</h4>
    <ul>
      ${exp.reasons.map(r => `<li>${escapeHtml(r)}</li>`).join("")}
    </ul>
    <h4>Raw links</h4>
    <p><strong>Linear:</strong> ${escapeHtml(row.linear_issue_key || "")}</p>
    <p><strong>GitHub:</strong> ${row.pr_url ? `<a href="${escapeAttr(row.pr_url)}" target="_blank">Merged PR</a>` : "No merged PR found"}</p>
    <p><strong>Slack blocker:</strong> ${escapeHtml(row.latest_blocker || "None")}</p>
    <p><strong>Support:</strong> ${escapeHtml(row.latest_support_subject || "None")}</p>
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
