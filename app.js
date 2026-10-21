// app.js - Frontend for Top 100 Pure-Play Digital AI Companies 2026

const fmtB = (x) => x == null ? "—" : "$" + Number(x).toLocaleString() + "B";
const fmtM = (x) => x == null ? "—" : "$" + Number(x).toLocaleString() + "M";
const fmtNum = (x, suffix = "") => x == null ? "—" : Number(x).toLocaleString() + suffix;

// Valuation basis taxonomy - the core of the big-tech rationalisation.
const BASIS = {
  actual:  { short: "Pure-play", full: "Pure-play AI - market-set AI valuation, used as-is" },
  derived: { short: "AI-attributed", full: "AI-attributed - valuation derived as AI ARR x peer multiple" },
  proxy:   { short: "Proxy", full: "Market-cap proxy - no AI revenue disclosure, weakest evidence" },
};

// State
let allRows = [];
let filteredRows = [];
let sortKey = "rank";
let sortDir = "asc";

async function loadData() {
  const res = await fetch("ranked.json", { cache: "no-store" });
  const data = await res.json();
  allRows = data.companies;
  filteredRows = [...allRows];
  return data;
}

function applyFilters(filters) {
  const q = (filters.query || "").toLowerCase().trim();
  const cat = filters.category || "";
  const basis = filters.basis || "";
  filteredRows = allRows.filter((r) => {
    const text = (
      r.name + " " + (r.category || "") + " " + (r.hq || "") + " " +
      (r.summary || "")
    ).toLowerCase();
    if (q && !text.includes(q)) return false;
    if (cat && r.category !== cat) return false;
    if (basis && r.valuation_basis !== basis) return false;
    return true;
  });
}

function sortRows(key, dir) {
  const sign = dir === "asc" ? 1 : -1;
  filteredRows.sort((a, b) => {
    let av = a[key], bv = b[key];
    if (av == null) av = -Infinity;
    if (bv == null) bv = -Infinity;
    if (typeof av === "string" && typeof bv === "string") {
      return av.localeCompare(bv) * sign;
    }
    return (Number(av) - Number(bv)) * sign;
  });
}

function renderTable() {
  const tbody = document.querySelector("table.rank tbody");
  tbody.innerHTML = "";
  const max = Math.max(...filteredRows.map((r) => r.score || 0), 100);
  filteredRows.forEach((r) => {
    const tr = document.createElement("tr");
    const medalClass =
      r.rank === 1 ? "gold" : r.rank === 2 ? "silver" : r.rank === 3 ? "bronze" : "";
    const medalLabel = medalClass ? r.rank : r.rank;
    tr.innerHTML = `
      <td class="rank-cell">
        <span class="medal ${medalClass}">${medalLabel}</span>
      </td>
      <td class="name-cell">
        <strong><a href="company.html?id=${encodeURIComponent(r.name)}">${escapeHtml(r.name)}</a></strong>
        <span class="meta">${escapeHtml(r.hq || "")} • ${escapeHtml(String(r.founded || "—"))}</span>
      </td>
      <td><span class="cat-chip">${escapeHtml(r.category || "—")}</span></td>
      <td class="num">
        ${fmtB(r.valuation_usd_b)}
        ${r.valuation_basis === "derived"
          ? `<div class="sub-note">${BASIS.derived.short} · mkt cap ${fmtB(r.market_cap_usd_b)}</div>`
          : r.valuation_basis === "proxy"
            ? `<div class="sub-note warn">${BASIS.proxy.short} · mkt cap ${fmtB(r.market_cap_usd_b)}</div>`
            : ""}
      </td>
      <td class="num">
        ${fmtM(r.arr_usd_m)}
        ${r.valuation_basis !== "actual"
          ? `<div class="sub-note">AI-attributed</div>` : ""}
      </td>
      <td class="score-cell">
        ${r.score.toFixed(1)}
        <span class="score-bar" style="width:${Math.max(2, (r.score / max) * 80)}px"></span>
      </td>
    `;
    tbody.appendChild(tr);
  });
  document.getElementById("showing").textContent =
    `Showing ${filteredRows.length} of ${allRows.length}`;
}

function escapeHtml(s) {
  return String(s || "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;"
  })[c]);
}

function uniqueCategories() {
  return [...new Set(allRows.map((r) => r.category).filter(Boolean))].sort();
}

function fillCategorySelect() {
  const sel = document.querySelector("select[data-filter='category']");
  if (!sel) return;
  uniqueCategories().forEach((c) => {
    const opt = document.createElement("option");
    opt.value = c;
    opt.textContent = c;
    sel.appendChild(opt);
  });
}

function updateHeaderArrows() {
  document.querySelectorAll("table.rank thead th[data-key]").forEach((th) => {
    th.classList.remove("sorted-asc", "sorted-desc");
    if (th.dataset.key === sortKey) {
      th.classList.add(sortDir === "asc" ? "sorted-asc" : "sorted-desc");
    }
  });
}

function attachSortHandlers() {
  document.querySelectorAll("table.rank thead th[data-key]").forEach((th) => {
    th.addEventListener("click", () => {
      const key = th.dataset.key;
      if (sortKey === key) {
        sortDir = sortDir === "asc" ? "desc" : "asc";
      } else {
        sortKey = key;
        sortDir = "asc";
      }
      sortRows(sortKey, sortDir);
      renderTable();
      updateHeaderArrows();
    });
  });
}

function attachFilterHandlers() {
  const qInput = document.querySelector("input[data-filter='query']");
  const cSel = document.querySelector("select[data-filter='category']");
  const bSel = document.querySelector("select[data-filter='basis']");
  const apply = () => {
    applyFilters({
      query: qInput?.value || "",
      category: cSel?.value || "",
      basis: bSel?.value || "",
    });
    sortRows(sortKey, sortDir);
    renderTable();
  };
  qInput?.addEventListener("input", apply);
  cSel?.addEventListener("change", apply);
  bSel?.addEventListener("change", apply);
}

function exportCsv() {
  const rows = ["rank,name,category,hq,founded,valuation_usd_b,arr_usd_m,score"];
  filteredRows.forEach((r) => {
    rows.push([
      r.rank,
      JSON.stringify(r.name),
      JSON.stringify(r.category || ""),
      JSON.stringify(r.hq || ""),
      r.founded || "",
      r.valuation_usd_b ?? "",
      r.arr_usd_m ?? "",
      r.score,
    ].join(","));
  });
  const blob = new Blob([rows.join("\n")], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "top100_digital_ai_2026.csv";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function attachExportHandler() {
  document.querySelectorAll("[data-action='export-csv']").forEach((b) => {
    b.addEventListener("click", exportCsv);
  });
}

function setActiveNav() {
  const path = location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".nav a").forEach((a) => {
    if (a.getAttribute("href") === path) a.classList.add("active");
  });
}

async function init() {
  setActiveNav();
  const data = await loadData();

  // Hero stats if present
  const heroCompanies = document.getElementById("hero-companies");
  if (heroCompanies) heroCompanies.textContent = data.counts.ranked;
  const heroAxes = document.getElementById("hero-axes");
  if (heroAxes) {
    const v = data.axes.valuation_usd_b;
    const a = data.axes.arr_usd_m;
    heroAxes.innerHTML = `Val $${Math.pow(10, v.log_min).toFixed(2)}B &ndash; $${Math.pow(10, v.log_max).toFixed(0)}B, ARR $${Math.pow(10, a.log_min).toFixed(1)}M &ndash; $${Math.pow(10, a.log_max).toFixed(0)}M`;
  }

  // The ranking table only exists on ranking.html
  const tbody = document.querySelector("table.rank tbody");
  if (!tbody) return;

  fillCategorySelect();
  attachSortHandlers();
  attachFilterHandlers();
  attachExportHandler();
  sortRows(sortKey, sortDir);
  renderTable();
  updateHeaderArrows();
}

// Detail page logic
async function initDetail() {
  setActiveNav();
  const params = new URLSearchParams(location.search);
  const id = params.get("id");
  if (!id) {
    document.getElementById("detail").innerHTML = "<p>No company id provided.</p>";
    return;
  }
  const data = await loadData();
  const c = allRows.find((r) => r.name === id);
  if (!c) {
    document.getElementById("detail").innerHTML = "<p>Company not found.</p>";
    return;
  }
  document.title = `${c.name} - Top 100 Digital AI Companies 2026`;
  const root = document.getElementById("detail");
  const basis = BASIS[c.valuation_basis] || BASIS.actual;
  const pm = data.peer_multiple || {};

  const valuationBlock = c.valuation_basis === "derived" ? `
    <div class="basis-callout">
      <h3>Derived AI valuation</h3>
      <p>
        ${escapeHtml(c.name)} is a diversified company, so its market cap prices a
        much larger non-AI business. We value only its
        <strong>AI-attributed ARR</strong> at the pure-play median EV/Revenue
        multiple, and use that as the valuation axis.
      </p>
      <pre>AI-attributed ARR      = ${fmtM(c.arr_usd_m)}
peer median multiple    = ${pm.median_ev_revenue ?? "—"}x   (n=${pm.pool_size ?? "—"} pure-play companies)
implied AI valuation    = ${fmtM(c.arr_usd_m)} x ${pm.median_ev_revenue ?? "—"}x
                        = $${((c.arr_usd_m * (pm.median_ev_revenue || 0)) / 1000).toLocaleString(undefined, { maximumFractionDigits: 1 })}B</pre>
      <p class="sub-note">
        Full-company market cap for reference: <strong>${fmtB(c.market_cap_usd_b)}</strong>
        ${c.market_cap_date ? "(" + escapeHtml(c.market_cap_date) + ")" : ""}.
        The gap between the two is the part of the company that is <em>not</em> AI.
      </p>
    </div>
  ` : c.valuation_basis === "proxy" ? `
    <div class="basis-callout warn">
      <h3>Market-cap proxy</h3>
      <p>
        ${escapeHtml(c.name)} does not disclose AI-attributed revenue, so no AI
        valuation can be derived. We use the <strong>full market cap</strong> as a
        flagged proxy and score the ARR axis at zero. This simultaneously
        <em>overstates</em> its AI valuation and <em>understates</em> its AI revenue,
        so treat this row as the weakest evidence in the list.
      </p>
      <p class="sub-note">Full-company market cap: <strong>${fmtB(c.market_cap_usd_b)}</strong>
        ${c.market_cap_date ? "(" + escapeHtml(c.market_cap_date) + ")" : ""}</p>
    </div>
  ` : `
    <div class="basis-callout pure">
      <h3>Pure-play AI valuation</h3>
      <p>
        ${escapeHtml(c.name)} is an AI company. Its market or transaction
        valuation <strong>is</strong> an AI valuation and is used as-is &mdash;
        no adjustment applied.
      </p>
    </div>
  `;

  root.innerHTML = `
    <div>
      <div class="card">
        <div class="row between">
          <div>
            <span class="eyebrow">Rank #${c.rank} of ${data.counts.ranked}</span>
            <h1>${escapeHtml(c.name)}</h1>
            <p class="subtitle">${escapeHtml(c.summary || "")}</p>
            <span class="cat-chip basis-chip basis-${c.valuation_basis}">${escapeHtml(basis.short)}</span>
            <span class="sub-note" style="display:inline;margin-left:8px;">${escapeHtml(basis.full)}</span>
          </div>
          <div class="score-cell" style="font-size:32px;color:var(--accent);">${c.score.toFixed(1)}</div>
        </div>
        <div class="hero-stats" style="border-top:1px solid var(--border);">
          <div class="stat"><span class="v">${fmtB(c.valuation_usd_b)}</span><span class="l">${c.valuation_basis === "actual" ? "Valuation" : c.valuation_basis === "derived" ? "Implied AI valuation" : "Market cap (proxy)"}</span></div>
          <div class="stat"><span class="v">${fmtM(c.arr_usd_m)}</span><span class="l">AI-attributed ARR</span></div>
          <div class="stat"><span class="v">${c.z_val != null ? c.z_val.toFixed(2) : "—"}</span><span class="l">Valuation z-score (log)</span></div>
          <div class="stat"><span class="v">${c.z_arr != null ? c.z_arr.toFixed(2) : "—"}</span><span class="l">ARR z-score (log)</span></div>
        </div>
      </div>

      ${valuationBlock}

      <div class="card">
        <h2>About</h2>
        <p>${escapeHtml(c.summary || "")}</p>
        <p style="margin-top:14px;color:var(--text-dim);">
          <strong>Headquarters:</strong> ${escapeHtml(c.hq || "—")}<br>
          <strong>Founded:</strong> ${escapeHtml(String(c.founded || "—"))}<br>
          <strong>Category:</strong> <span class="cat-chip">${escapeHtml(c.category || "—")}</span>
        </p>
        ${c.corporate_status ? `<p style="margin-top:12px;color:var(--warn);"><strong>Corporate status:</strong> ${escapeHtml(c.corporate_status)}</p>` : ""}
      </div>

      <div class="card">
        <h2>Scoring detail</h2>
        <p>
          ${escapeHtml(c.name)} scored <strong>${c.score.toFixed(2)} / 100</strong> on the
          Top 100 Pure-Play Digital AI Companies 2026 composite.
        </p>
        <p>
          The composite is built from a 50/50 weighted sum of the valuation axis and the
          ARR axis after log-min-max normalisation. Higher scores mean the company sits
          closer to the upper bound of both axes.
        </p>
        <pre style="margin-top:14px;">score = 100 * ( 0.5 * z_val(${c.z_val != null ? c.z_val.toFixed(4) : "0.0000"}) +
                0.5 * z_arr(${c.z_arr != null ? c.z_arr.toFixed(4) : "0.0000"}) )
       = ${c.score.toFixed(2)}</pre>
        ${c.missing_axes ? `<p style="color:var(--warn);">Note: ${escapeHtml(c.missing_axes)} data was unavailable; the missing axis was scored at 0 (worst observed).</p>` : ""}
      </div>

      <div class="card">
        <h2>Sources</h2>
        <h3>Valuation</h3>
        <div class="src-block">${escapeHtml(c.valuation_source || "—")}</div>
        <h3>ARR</h3>
        <div class="src-block">${escapeHtml(c.arr_source || "—")}</div>
        ${c.arr_attribution_note ? `<h3>AI-attribution note</h3><div class="src-block">${escapeHtml(c.arr_attribution_note)}</div>` : ""}
      </div>
    </div>

    <aside class="detail-side">
      <h3>Valuation</h3>
      <div class="v">${fmtB(c.valuation_usd_b)}</div>
      <div class="src">${c.valuation_basis === "actual" ? "Market-set AI valuation" : c.valuation_basis === "derived" ? "Derived from AI ARR x peer multiple" : "Market-cap proxy (flagged)"}</div>
      <div class="src">${escapeHtml(c.valuation_date || "—")}</div>
      ${c.market_cap_usd_b ? `<div class="src" style="margin-top:6px;">Full-company market cap: ${fmtB(c.market_cap_usd_b)}</div>` : ""}

      <h3>ARR / Revenue</h3>
      <div class="v">${fmtM(c.arr_usd_m)}</div>
      <div class="src">AI-attributed</div>
      <div class="src">${escapeHtml(c.arr_date || "—")}</div>

      <h3>Quick links</h3>
      <a href="ranking.html">← Back to full ranking</a>
    </aside>
  `;
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.body.dataset.page === "detail") initDetail();
  else init();
});
