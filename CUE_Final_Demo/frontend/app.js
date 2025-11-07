// const API_BASE = "http://127.0.0.1:8000";

// // Elements
// const accountSelect = document.getElementById("account-select");
// const btnGenerate = document.getElementById("btn-generate");

// const tabBrief = document.getElementById("tab-brief");
// const tabTrends = document.getElementById("tab-trends");
// const briefView = document.getElementById("brief-view");
// const trendsView = document.getElementById("trends-view");

// // Summary
// const summaryRisk = document.getElementById("summary-risk");
// const summaryGuardrails = document.getElementById("summary-guardrails");
// const summaryCoverage = document.getElementById("summary-coverage");

// // Brief
// const briefTitle = document.getElementById("brief-title");
// const briefRiskPill = document.getElementById("brief-risk-pill");

// const highlightsList = document.getElementById("highlights-list");
// const risksList = document.getElementById("risks-list");
// const escalationsList = document.getElementById("escalations-list");
// const commitmentsList = document.getElementById("commitments-list");
// const citationsBlock = document.getElementById("citations-block");

// // Trends
// const trendsTitle = document.getElementById("trends-title");
// const trendsSummary = document.getElementById("trends-summary");
// const trendsTableBody = document.querySelector("#trends-table tbody");

// let trendsCache = null;

// // Init
// document.addEventListener("DOMContentLoaded", () => {
//   loadAccounts();
//   wireEvents();
// });

// // ---- Load accounts ----

// async function loadAccounts() {
//   try {
//     const res = await fetch(`${API_BASE}/accounts`);
//     if (!res.ok) throw new Error(`HTTP ${res.status}`);
//     const data = await res.json();
//     const accounts = data.accounts || [];

//     accountSelect.innerHTML = "";
//     accounts.forEach((name) => {
//       const opt = document.createElement("option");
//       opt.value = name;
//       opt.textContent = name;
//       accountSelect.appendChild(opt);
//     });

//     if (accounts.length) {
//       await loadBrief(accounts[0]);
//     } else {
//       briefTitle.textContent = "No accounts found in Chroma.";
//     }
//   } catch (err) {
//     console.error("Error loading accounts", err);
//     briefTitle.textContent = `Error loading accounts: ${err.message}`;
//   }
// }

// // ---- Events ----

// function wireEvents() {
//   if (btnGenerate) {
//     btnGenerate.addEventListener("click", () => {
//       const account = accountSelect.value;
//       if (account) loadBrief(account);
//     });
//   }

//   if (tabBrief && tabTrends) {
//     tabBrief.addEventListener("click", () => {
//       tabBrief.classList.add("active");
//       tabTrends.classList.remove("active");
//       briefView.style.display = "block";
//       trendsView.style.display = "none";
//     });

//     tabTrends.addEventListener("click", () => {
//       tabTrends.classList.add("active");
//       tabBrief.classList.remove("active");
//       briefView.style.display = "none";
//       trendsView.style.display = "block";
//       loadTrends();
//     });
//   }

//   if (accountSelect) {
//     accountSelect.addEventListener("change", () => {
//       if (tabBrief.classList.contains("active")) {
//         loadBrief(accountSelect.value);
//       }
//     });
//   }
// }

// // ---- Load brief ----

// async function loadBrief(account) {
//   setLoadingState(true, `Generating brief for ${account}...`);

//   try {
//     const res = await fetch(
//       `${API_BASE}/brief/${encodeURIComponent(account)}`
//     );
//     if (!res.ok) {
//       throw new Error(`HTTP ${res.status}`);
//     }
//     const data = await res.json();

//     renderSummary(data);
//     renderBrief(account, data);
//   } catch (err) {
//     console.error("Error loading brief", err);
//     briefTitle.textContent = `Error generating brief: ${err.message}`;
//   } finally {
//     setLoadingState(false);
//   }
// }

// function setLoadingState(isLoading, msg) {
//   if (isLoading) {
//     briefTitle.textContent = msg || "Loading...";
//     btnGenerate.disabled = true;
//     btnGenerate.textContent = "Loading...";
//   } else {
//     btnGenerate.disabled = false;
//     btnGenerate.textContent = "Generate / Refresh Brief";
//   }
// }

// // ---- Render summary ----

// function renderSummary(data) {
//   const risk = (data.risk_level || "—").toString();
//   const cov = data.coverage?.ratio ?? null;
//   const guardOk = data.guardrails?.ok;

//   // sidebar risk
//   summaryRisk.textContent = risk;
//   summaryRisk.className = "pill " + riskPillClass(risk);

//   // guardrails
//   if (guardOk === true) {
//     summaryGuardrails.textContent = "OK";
//     summaryGuardrails.className = "pill pill-ok";
//   } else if (guardOk === false) {
//     summaryGuardrails.textContent = "Check";
//     summaryGuardrails.className = "pill pill-bad";
//   } else {
//     summaryGuardrails.textContent = "—";
//     summaryGuardrails.className = "pill pill-muted";
//   }

//   // coverage
//   if (typeof cov === "number") {
//     summaryCoverage.textContent = `${Math.round(cov * 100)}%`;
//     summaryCoverage.className = "pill pill-ok";
//   } else {
//     summaryCoverage.textContent = "—";
//     summaryCoverage.className = "pill pill-muted";
//   }
// }

// // ---- Render brief cards ----

// function renderBrief(account, data) {
//   const md = data.markdown || "";
//   briefTitle.textContent = `Customer Brief — ${account} (last 30 days)`;

//   // Risk pill
//   const risk = (data.risk_level || "").toLowerCase();
//   briefRiskPill.textContent = `Risk: ${data.risk_level || "—"}`;
//   briefRiskPill.className = "risk-pill " + {
//     low: "risk-pill-low",
//     medium: "risk-pill-medium",
//     high: "risk-pill-high",
//   }[risk] || "risk-pill-none";

//   // Naive section parsing from markdown
//   const sections = splitSections(md);

//   fillList(highlightsList, sections.highlights);
//   fillList(risksList, sections.risks);
//   fillList(escalationsList, sections.escalations);
//   fillList(commitmentsList, sections.commits);

//   citationsBlock.textContent = sections.citations || "No citations found.";
// }

// function fillList(ul, items) {
//   ul.innerHTML = "";
//   if (!items || !items.length) {
//     ul.classList.add("empty");
//     ul.innerHTML = "<li>No data.</li>";
//     return;
//   }
//   ul.classList.remove("empty");
//   items.forEach((t) => {
//     const li = document.createElement("li");
//     li.textContent = t.replace(/^-\s*/, "");
//     ul.appendChild(li);
//   });
// }

// // Extract sections from the markdown your backend generates
// function splitSections(md) {
//   const lines = md.split("\n");

//   const out = {
//     highlights: [],
//     risks: [],
//     commits: [],
//     escalations: [],
//     citations: "",
//   };

//   let current = null;

//   for (const raw of lines) {
//     const line = raw.trim();

//     if (/^Top Risks$/i.test(line)) {
//       current = "risks";
//       continue;
//     }
//     if (/^Open Commitments$/i.test(line)) {
//       current = "commits";
//       continue;
//     }
//     if (/^Recent Escalations$/i.test(line)) {
//       current = "escalations";
//       continue;
//     }
//     if (/^Highlights$/i.test(line)) {
//       current = "highlights";
//       continue;
//     }
//     if (/^Citations$/i.test(line)) {
//       current = "citations";
//       continue;
//     }

//     if (current === "citations") {
//       out.citations += raw + "\n";
//     } else if (current && line.startsWith("-")) {
//       out[current].push(line);
//     }
//   }

//   out.citations = out.citations.trim();
//   return out;
// }

// function riskPillClass(risk) {
//   const r = risk.toLowerCase();
//   if (r === "low") return "pill-ok";
//   if (r === "medium") return "pill-muted";
//   if (r === "high") return "pill-bad";
//   return "pill-muted";
// }

// // ---- Trends ----

// async function loadTrends() {
//   // Cache to avoid re-fetch on each tab click
//   if (trendsCache) {
//     renderTrends(trendsCache);
//     return;
//   }

//   trendsSummary.textContent = "Loading trends...";
//   trendsTableBody.innerHTML = "";

//   try {
//     const res = await fetch(`${API_BASE}/trends`);
//     if (!res.ok) {
//       throw new Error(`HTTP ${res.status}`);
//     }
//     const data = await res.json();
//     const trends = data.trends || data || [];
//     trendsCache = trends;
//     renderTrends(trends);
//   } catch (err) {
//     console.error("Error loading trends", err);
//     trendsSummary.textContent = `Error loading trends: ${err.message}`;
//   }
// }

// function renderTrends(trends) {
//   if (!Array.isArray(trends) || trends.length === 0) {
//     trendsSummary.textContent =
//       "No trends data yet. Generate briefs and export trends.";
//     return;
//   }

//   // Summary counts
//   const counts = trends.reduce(
//     (acc, row) => {
//       const r = (row.risk_level || "").toLowerCase();
//       if (r === "high") acc.high++;
//       else if (r === "medium") acc.medium++;
//       else if (r === "low") acc.low++;
//       return acc;
//     },
//     { low: 0, medium: 0, high: 0 }
//   );

//   trendsSummary.innerHTML = `
//     <div class="trend-card">
//       <div class="label">Low Risk</div>
//       <div class="value">${counts.low}</div>
//     </div>
//     <div class="trend-card">
//       <div class="label">Medium Risk</div>
//       <div class="value">${counts.medium}</div>
//     </div>
//     <div class="trend-card">
//       <div class="label">High Risk</div>
//       <div class="value">${counts.high}</div>
//     </div>
//   `;

//   // Table rows
//   trendsTableBody.innerHTML = "";
//   trends.forEach((row) => {
//     const tr = document.createElement("tr");

//     const coveragePct =
//       typeof row.coverage_ratio === "number"
//         ? `${Math.round(row.coverage_ratio * 100)}%`
//         : "";

//     const guardrailsPct =
//       typeof row.guardrails_ok === "number"
//         ? `${Math.round(row.guardrails_ok * 100)}%`
//         : row.guardrails_ok === true
//         ? "100%"
//         : row.guardrails_ok === false
//         ? "0%"
//         : "";

//     tr.innerHTML = `
//       <td>${row.account || ""}</td>
//       <td>${riskBadge(row.risk_level)}</td>
//       <td>${coveragePct}</td>
//       <td>${guardrailsPct}</td>
//       <td>${formatTs(row.ts)}</td>
//     `;
//     trendsTableBody.appendChild(tr);
//   });
// }

// function riskBadge(level) {
//   const r = (level || "").toLowerCase();
//   if (r === "low")
//     return `<span class="pill pill-ok">Low</span>`;
//   if (r === "medium")
//     return `<span class="pill pill-muted">Medium</span>`;
//   if (r === "high")
//     return `<span class="pill pill-bad">High</span>`;
//   return `<span class="pill pill-muted">—</span>`;
// }

// function formatTs(ts) {
//   if (!ts) return "";
//   const d = new Date(ts);
//   if (Number.isNaN(d.getTime())) return ts;
//   return d.toLocaleString();
// }



const API_BASE = "http://127.0.0.1:8000";

// Elements
const accountSelect = document.getElementById("account-select");
const btnGenerate = document.getElementById("btn-generate");

const tabBrief = document.getElementById("tab-brief");
const tabTrends = document.getElementById("tab-trends");
const briefView = document.getElementById("brief-view");
const trendsView = document.getElementById("trends-view");

// Summary
const summaryRisk = document.getElementById("summary-risk");
const summaryGuardrails = document.getElementById("summary-guardrails");
const summaryCoverage = document.getElementById("summary-coverage");

// Brief
const briefTitle = document.getElementById("brief-title");
const briefRiskPill = document.getElementById("brief-risk-pill");
const highlightsList = document.getElementById("highlights-list");
const risksList = document.getElementById("risks-list");
const escalationsList = document.getElementById("escalations-list");
const commitmentsList = document.getElementById("commitments-list");
const citationsBlock = document.getElementById("citations-block");

// Trends
const trendsTitle = document.getElementById("trends-title");
const trendsSummary = document.getElementById("trends-summary");
const trendsTableBody = document.querySelector("#trends-table tbody");

// Alerts banner (top of Trends / page header)
const alertBanner = document.getElementById("alert-banner");

// // Ask CUE chat
// const askInput = document.getElementById("ask-input");
// const askButton = document.getElementById("ask-send");
// const askThread = document.getElementById("ask-thread");

let trendsCache = null;

// Init
document.addEventListener("DOMContentLoaded", () => {
  loadAccounts();
  wireEvents();
  loadAlerts(); // portfolio risk banner
});

// ---- Load accounts ----

async function loadAccounts() {
  try {
    const res = await fetch(`${API_BASE}/accounts`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const accounts = data.accounts || [];

    accountSelect.innerHTML = "";
    accounts.forEach((name) => {
      const opt = document.createElement("option");
      opt.value = name;
      opt.textContent = name;
      accountSelect.appendChild(opt);
    });

    if (accounts.length) {
      await loadBrief(accounts[0]);
    } else {
      briefTitle.textContent = "No accounts found in Chroma.";
    }
  } catch (err) {
    console.error("Error loading accounts", err);
    briefTitle.textContent = `Error loading accounts: ${err.message}`;
  }
}

// ---- Events ----

function wireEvents() {
  if (btnGenerate) {
    btnGenerate.addEventListener("click", () => {
      const account = accountSelect.value;
      if (account) loadBrief(account);
    });
  }

  if (tabBrief && tabTrends) {
    tabBrief.addEventListener("click", () => {
      tabBrief.classList.add("active");
      tabTrends.classList.remove("active");
      briefView.style.display = "block";
      trendsView.style.display = "none";
    });

    tabTrends.addEventListener("click", () => {
      tabTrends.classList.add("active");
      tabBrief.classList.remove("active");
      briefView.style.display = "none";
      trendsView.style.display = "block";
      loadTrends();
    });
  }

  if (accountSelect) {
    accountSelect.addEventListener("change", () => {
      if (tabBrief.classList.contains("active")) {
        loadBrief(accountSelect.value);
      }
    });
  }

  // Ask CUE interactions
  if (askButton && askInput && askThread) {
    askButton.addEventListener("click", () => {
      const q = askInput.value.trim();
      if (!q) return;
      const account = accountSelect.value;
      askCue(account, q);
    });

    askInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        askButton.click();
      }
    });
  }
}

// ---- Load brief ----

async function loadBrief(account) {
  setLoadingState(true, `Generating brief for ${account}...`);

  try {
    const res = await fetch(
      `${API_BASE}/brief/${encodeURIComponent(account)}`
    );
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    const data = await res.json();

    renderSummary(data);
    renderBrief(account, data);
  } catch (err) {
    console.error("Error loading brief", err);
    briefTitle.textContent = `Error generating brief: ${err.message}`;
  } finally {
    setLoadingState(false);
  }
}

function setLoadingState(isLoading, msg) {
  if (isLoading) {
    briefTitle.textContent = msg || "Loading...";
    if (btnGenerate) {
      btnGenerate.disabled = true;
      btnGenerate.textContent = "Loading...";
    }
  } else if (btnGenerate) {
    btnGenerate.disabled = false;
    btnGenerate.textContent = "Generate / Refresh Brief";
  }
}

// ---- Render summary ----

function renderSummary(data) {
  const risk = (data.risk_level || "—").toString();
  const cov = data.coverage?.ratio ?? null;
  const guardOk = data.guardrails?.ok;

  summaryRisk.textContent = risk;
  summaryRisk.className = "pill " + riskPillClass(risk);

  if (guardOk === true) {
    summaryGuardrails.textContent = "OK";
    summaryGuardrails.className = "pill pill-ok";
  } else if (guardOk === false) {
    summaryGuardrails.textContent = "Check";
    summaryGuardrails.className = "pill pill-bad";
  } else {
    summaryGuardrails.textContent = "—";
    summaryGuardrails.className = "pill pill-muted";
  }

  if (typeof cov === "number") {
    summaryCoverage.textContent = `${Math.round(cov * 100)}%`;
    summaryCoverage.className = "pill pill-ok";
  } else {
    summaryCoverage.textContent = "—";
    summaryCoverage.className = "pill pill-muted";
  }
}

// ---- Render brief cards ----

function renderBrief(account, data) {
  const md = data.markdown || "";
  briefTitle.textContent = `Customer Brief — ${account} (last 30 days)`;

  const risk = (data.risk_level || "").toLowerCase();
  briefRiskPill.textContent = `Risk: ${data.risk_level || "—"}`;
  briefRiskPill.className =
    "risk-pill " +
    ({
      low: "risk-pill-low",
      medium: "risk-pill-medium",
      high: "risk-pill-high",
    }[risk] || "risk-pill-none");

  const sections = splitSections(md);

  fillList(highlightsList, sections.highlights);
  fillList(risksList, sections.risks);
  fillList(escalationsList, sections.escalations);
  fillList(commitmentsList, sections.commits);

  citationsBlock.textContent = sections.citations || "No citations found.";
}

function fillList(ul, items) {
  if (!ul) return;
  ul.innerHTML = "";
  if (!items || !items.length) {
    ul.classList.add("empty");
    ul.innerHTML = "<li>No data.</li>";
    return;
  }
  ul.classList.remove("empty");
  items.forEach((t) => {
    const li = document.createElement("li");
    li.textContent = t.replace(/^-\s*/, "");
    ul.appendChild(li);
  });
}

// ---- Markdown section parsing ----

function splitSections(md) {
  const lines = md.split("\n");

  const out = {
    highlights: [],
    risks: [],
    commits: [],
    escalations: [],
    citations: "",
  };

  let current = null;

  for (const raw of lines) {
    const line = raw.trim();

    if (/^Top Risks$/i.test(line)) {
      current = "risks";
      continue;
    }
    if (/^Open Commitments$/i.test(line)) {
      current = "commits";
      continue;
    }
    if (/^Recent Escalations$/i.test(line)) {
      current = "escalations";
      continue;
    }
    if (/^Highlights$/i.test(line)) {
      current = "highlights";
      continue;
    }
    if (/^Citations$/i.test(line)) {
      current = "citations";
      continue;
    }

    if (current === "citations") {
      out.citations += raw + "\n";
    } else if (current && line.startsWith("-")) {
      out[current].push(line);
    }
  }

  out.citations = out.citations.trim();
  return out;
}

function riskPillClass(risk) {
  const r = (risk || "").toLowerCase();
  if (r === "low") return "pill-ok";
  if (r === "medium") return "pill-muted";
  if (r === "high") return "pill-bad";
  return "pill-muted";
}

// ---- Trends ----

async function loadTrends() {
  if (trendsCache) {
    renderTrends(trendsCache);
    return;
  }

  trendsSummary.textContent = "Loading trends...";
  trendsTableBody.innerHTML = "";

  try {
    const res = await fetch(`${API_BASE}/trends`);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    const data = await res.json();
    const trends = data.trends || data || [];
    trendsCache = trends;
    renderTrends(trends);
  } catch (err) {
    console.error("Error loading trends", err);
    trendsSummary.textContent = `Error loading trends: ${err.message}`;
  }
}

function renderTrends(trends) {
  if (!Array.isArray(trends) || trends.length === 0) {
    trendsSummary.textContent =
      "No trends data yet. Generate briefs and export trends.";
    trendsTableBody.innerHTML = "";
    return;
  }

  const counts = trends.reduce(
    (acc, row) => {
      const r = (row.risk_level || "").toLowerCase();
      if (r === "high") acc.high++;
      else if (r === "medium") acc.medium++;
      else if (r === "low") acc.low++;
      return acc;
    },
    { low: 0, medium: 0, high: 0 }
  );

  trendsSummary.innerHTML = `
    <div class="trend-card">
      <div class="label">Low Risk</div>
      <div class="value">${counts.low}</div>
    </div>
    <div class="trend-card">
      <div class="label">Medium Risk</div>
      <div class="value">${counts.medium}</div>
    </div>
    <div class="trend-card">
      <div class="label">High Risk</div>
      <div class="value">${counts.high}</div>
    </div>
  `;

  trendsTableBody.innerHTML = "";
  trends.forEach((row) => {
    const tr = document.createElement("tr");

    const coveragePct =
      typeof row.coverage_ratio === "number"
        ? `${Math.round(row.coverage_ratio * 100)}%`
        : "";

    const guardrailsPct =
      typeof row.guardrails_ok === "number"
        ? `${Math.round(row.guardrails_ok * 100)}%`
        : row.guardrails_ok === true
        ? "100%"
        : row.guardrails_ok === false
        ? "0%"
        : "";

    tr.innerHTML = `
      <td>${row.account || ""}</td>
      <td>${riskBadge(row.risk_level)}</td>
      <td>${coveragePct}</td>
      <td>${guardrailsPct}</td>
      <td>${formatTs(row.ts)}</td>
    `;
    trendsTableBody.appendChild(tr);
  });
}

function riskBadge(level) {
  const r = (level || "").toLowerCase();
  if (r === "low") return `<span class="pill pill-ok">Low</span>`;
  if (r === "medium") return `<span class="pill pill-muted">Medium</span>`;
  if (r === "high") return `<span class="pill pill-bad">High</span>`;
  return `<span class="pill pill-muted">—</span>`;
}

function formatTs(ts) {
  if (!ts) return "";
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return ts;
  return d.toLocaleString();
}

// ---- Alerts banner ----

async function loadAlerts() {
  if (!alertBanner) return;
  try {
    const res = await fetch(`${API_BASE}/alerts`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const alerts = data.alerts || [];
    if (!alerts.length) {
      alertBanner.style.display = "none";
      return;
    }
    const bits = alerts.map(
      (a) => `${a.account}: ${a.risk_level}`
    );
    alertBanner.textContent = `⚠ Accounts at risk: ${bits.join(" • ")}`;
    alertBanner.style.display = "block";
  } catch (err) {
    console.error("Error loading alerts", err);
    alertBanner.style.display = "none";
  }
}

// // ---- Ask CUE ----

// async function askCue(account, question) {
//   appendAskBubble("user", question);
//   askInput.value = "";

//   try {
//     const res = await fetch(`${API_BASE}/ask`, {
//       method: "POST",
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify({ account, question }),
//     });
//     if (!res.ok) throw new Error(`HTTP ${res.status}`);
//     const data = await res.json();
//     appendAskBubble("cue", data.answer || "(No answer)");
//   } catch (err) {
//     console.error("Error asking CUE", err);
//     appendAskBubble("cue", `Sorry, I couldn't answer that: ${err.message}`);
//   }
// }

// function appendAskBubble(role, text) {
//   if (!askThread) return;
//   const div = document.createElement("div");
//   div.className = `ask-bubble ${role}`;
//   div.textContent = text;
//   askThread.appendChild(div);
//   askThread.scrollTop = askThread.scrollHeight;
// }


// ==== Ask CUE (chat) ====

const askThread = document.getElementById("ask-thread");
const askInput = document.getElementById("ask-input");
const askSend = document.getElementById("ask-send");

if (askThread && askInput && askSend) {
  askSend.addEventListener("click", handleAsk);
  askInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  });
}

if (askThread && askInput && askSend) {
  askSend.addEventListener("click", handleAsk);
  askInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  });
}

function appendAskBubble(who, text) {
  const div = document.createElement("div");
  div.className = `ask-bubble ${who}`;
  div.textContent = text;
  askThread.appendChild(div);
  askThread.scrollTop = askThread.scrollHeight;
}

// async function handleAsk() {
//   const q = askInput.value.trim();
//   const account = accountSelect.value;

//   if (!q || !account) return;

//   appendAskBubble("user", q);
//   askInput.value = "";

//   try {
//     const res = await fetch(`${API_BASE}/ask`, {
//       method: "POST",
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify({ account, question: q }),
//     });

//     if (!res.ok) {
//       throw new Error(`HTTP ${res.status}`);
//     }

//     const data = await res.json();
//     appendAskBubble("cue", data.answer || "I couldn't find an answer for that.");
//   } catch (err) {
//     console.error("Ask CUE error", err);
//     appendAskBubble(
//       "cue",
//       `I ran into an issue looking that up: ${err.message}`
//     );
//   }
// }

async function handleAsk() {
  const q = askInput.value.trim();
  const account = accountSelect.value;
  if (!q) return;

  appendAskBubble("user", q);
  askInput.value = "";

  // simple heuristic: if user asks portfolio-style question
  const isPortfolioQ = /(which|who|accounts|portfolio|overall|key clients|at risk)/i.test(q);

  try {
    const endpoint = isPortfolioQ ? "ask_portfolio" : "ask";
    const body = isPortfolioQ
      ? { question: q }
      : { account, question: q };

    const res = await fetch(`${API_BASE}/${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    // 🧩 1. Append CUE’s answer text first
    appendAskBubble("cue", data.answer || "(No answer)");

    // 🧩 2. Then show colored risk pills if portfolio data exists
    if (data.high_risk_accounts && Array.isArray(data.high_risk_accounts)) {
      data.high_risk_accounts.forEach(acc => {
        const badge = document.createElement("span");
        badge.className = `pill ${riskPillClass(acc.risk_level)}`;
        badge.textContent = `${acc.account} (${acc.risk_level})`;

        // optional: make clickable → load that account brief
        badge.style.cursor = "pointer";
        badge.addEventListener("click", () => {
          accountSelect.value = acc.account;
          tabBrief.click();
          loadBrief(acc.account);
        });

        askThread.appendChild(badge);
      });

      // auto-scroll so pills are visible
      askThread.scrollTop = askThread.scrollHeight;
    }

  } catch (err) {
    console.error("Ask CUE error", err);
    appendAskBubble("cue", `Error: ${err.message}`);
  }
}
