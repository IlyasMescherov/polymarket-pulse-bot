const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
const BOT_URL = "https://t.me/PulseMarketAIBot";
const POLYMARKET_URL = "https://polymarket.com";
const EMPTY_MESSAGE = "No data yet. PulseMarket will keep watching.";

if (tg) {
  tg.ready();
  tg.expand();
  if (tg.themeParams && tg.themeParams.bg_color) {
    document.documentElement.style.setProperty("--bg", tg.themeParams.bg_color);
  }
  if (tg.BackButton) {
    tg.BackButton.hide();
  }
}

const money = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function safeUrl(value) {
  const url = String(value || "");
  return url.startsWith("https://") ? url : POLYMARKET_URL;
}

function compactUsd(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "n/a";
  const number = Number(value);
  const abs = Math.abs(number);
  if (abs >= 1_000_000_000) return `$${(number / 1_000_000_000).toFixed(1)}B`;
  if (abs >= 1_000_000) return `$${(number / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `$${(number / 1_000).toFixed(0)}K`;
  return money.format(number);
}

function percent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "n/a";
  return `${Math.round(Number(value))}%`;
}

function movement(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "n/a";
  const rounded = Math.round(Number(value));
  const prefix = rounded > 0 ? "+" : "";
  return `${prefix}${rounded}%`;
}

function dataFrom(payload) {
  return Array.isArray(payload && payload.data) ? payload.data : [];
}

async function loadJson(path) {
  try {
    const response = await fetch(path, { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    return { data: [], message: EMPTY_MESSAGE };
  }
}

function clearNode(node) {
  node.classList.remove("skeleton-card");
  node.innerHTML = "";
}

function emptyState(message) {
  return `<div class="empty-state">${escapeHtml(message || EMPTY_MESSAGE)}</div>`;
}

function riskBadges(flags) {
  if (!Array.isArray(flags) || !flags.length) return "";
  return `
    <div class="small-meta">
      ${flags.slice(0, 3).map((flag) => `<span class="badge">${escapeHtml(flag)}</span>`).join("")}
    </div>
  `;
}

function metric(label, value, accent = false) {
  return `
    <div class="metric">
      <span>${escapeHtml(label)}</span>
      <strong class="${accent ? "accent-text" : ""}">${escapeHtml(value)}</strong>
    </div>
  `;
}

function scorePair(item) {
  return `
    <div class="score-pair">
      <div class="score-tile">
        <span>Pulse Score</span>
        <strong>${escapeHtml(item.pulse_score ?? 0)}/100 · ${escapeHtml(item.pulse_label || "Worth watching")}</strong>
      </div>
      <div class="score-tile">
        <span>Market Health</span>
        <strong>${escapeHtml(item.market_health_score ?? 0)}/100 · ${escapeHtml(item.market_health_label || "Healthy")}</strong>
      </div>
    </div>
  `;
}

function marketActions(item, primaryLabel = "Open Market") {
  const title = item.title || "PulseMarket AI market";
  const url = safeUrl(item.url);
  return `
    <div class="market-actions">
      <a class="market-action market-action--primary" href="${escapeHtml(url)}" target="_blank" rel="noreferrer">${escapeHtml(primaryLabel)}</a>
      <button class="market-action" type="button" data-bot-action="rules">Rules</button>
      <button class="market-action" type="button" data-bot-action="simple">Simple</button>
      <button class="market-action" type="button" data-share="${encodeURIComponent(title)}">Share</button>
    </div>
  `;
}

function marketSummaryCard(item, actionLabel = "Open") {
  return `
    <article class="market-card">
      <h3 class="market-title">${escapeHtml(item.title || "Untitled market")}</h3>
      <div class="small-meta">
        <span class="badge badge--accent">${percent(item.probability)}</span>
        <span class="badge">Move ${movement(item.movement)}</span>
        <span class="badge">${compactUsd(item.volume)}</span>
      </div>
      <div class="small-meta">
        <span class="badge">Pulse ${escapeHtml(item.pulse_score ?? 0)}/100</span>
        <span class="badge">Health ${escapeHtml(item.market_health_score ?? 0)}/100</span>
      </div>
      ${riskBadges(item.risk_flags)}
      <div class="card-link-row">
        <a href="${escapeHtml(safeUrl(item.url))}" target="_blank" rel="noreferrer">${escapeHtml(actionLabel)}</a>
        <button type="button" data-share="${encodeURIComponent(item.title || "PulseMarket AI")}">Share</button>
      </div>
    </article>
  `;
}

function searchResultCard(item) {
  return `
    <article class="search-card">
      <h3 class="market-title">${escapeHtml(item.title || "Untitled market")}</h3>
      <div class="small-meta">
        <span class="badge badge--accent">Probability ${percent(item.probability)}</span>
        <span class="badge">Pulse ${escapeHtml(item.pulse_score ?? 0)}/100</span>
        <span class="badge">Health ${escapeHtml(item.market_health_score ?? 0)}/100</span>
      </div>
      <p class="why-copy">A clean starting point for reading the market before opening Polymarket.</p>
      ${marketActions(item, "Open Market")}
    </article>
  `;
}

function renderToday(payload) {
  const hero = document.getElementById("today-hero");
  const secondary = document.getElementById("today-secondary");
  const items = dataFrom(payload);

  clearNode(hero);
  secondary.innerHTML = "";

  if (!items.length) {
    hero.innerHTML = emptyState("PulseMarket is preparing today’s intelligence.");
    return;
  }

  const top = items[0];
  hero.innerHTML = `
    <div>
      <p class="section-kicker">Main story today</p>
      <h3 class="market-title">${escapeHtml(top.title || "Untitled market")}</h3>
    </div>
    <div class="metric-row">
      ${metric("Probability", percent(top.probability), true)}
      ${metric("Movement", movement(top.movement))}
      ${metric("Volume", compactUsd(top.volume))}
    </div>
    ${scorePair(top)}
    <p class="why-copy">
      ${escapeHtml(top.why_it_matters || "High activity, meaningful score, and clean market data make this worth watching.")}
    </p>
    ${riskBadges(top.risk_flags)}
    ${marketActions(top)}
  `;

  secondary.innerHTML = items
    .slice(1, 3)
    .map((item) => marketSummaryCard(item, "Open"))
    .join("");
}

function renderSmart(payload) {
  const hero = document.getElementById("smart-hero");
  const items = dataFrom(payload);
  clearNode(hero);

  if (!items.length) {
    hero.innerHTML = emptyState("No strong public activity detected right now.");
    return;
  }

  const item = items[0];
  hero.innerHTML = `
    <div>
      <p class="section-kicker">Unusual public activity detected</p>
      <h3 class="market-title">${escapeHtml(item.title || "Public market activity")}</h3>
    </div>
    <div class="metric-row">
      ${metric("Public activity", compactUsd(item.public_activity), true)}
      ${metric("Public trades", item.trades_count ?? "n/a")}
      ${metric("View", item.top_side || "Market")}
    </div>
    <p class="why-copy">
      Large public activity can reveal where attention is moving before it becomes obvious.
    </p>
    <p class="micro-note">Research only · No trade execution</p>
    ${marketActions({ title: item.title, url: item.url }, "Explore Market")}
  `;
}

function renderHot(payload) {
  const target = document.getElementById("hot-strip");
  const items = dataFrom(payload);
  target.innerHTML = items.length
    ? items.slice(0, 6).map((item) => marketSummaryCard(item, "Open")).join("")
    : emptyState(payload.message || "No hot markets available yet.");
}

function renderMoves(payload) {
  const target = document.getElementById("moves-list");
  const items = dataFrom(payload);
  if (!items.length) {
    target.innerHTML = emptyState("No sharp movement story yet. PulseMarket will keep watching.");
    return;
  }

  target.innerHTML = items
    .slice(0, 5)
    .map(
      (item) => `
        <article class="move-card">
          <div>
            <h3 class="market-title">${escapeHtml(item.title || "Untitled market")}</h3>
            <div class="small-meta">
              <span class="badge">Probability ${percent(item.probability)}</span>
              <span class="badge">Pulse ${escapeHtml(item.pulse_score ?? 0)}/100</span>
            </div>
          </div>
          <span class="movement-pill">${movement(item.movement)}</span>
        </article>
      `,
    )
    .join("");
}

function renderSearch(payload) {
  const target = document.getElementById("search-results");
  const items = dataFrom(payload);
  target.innerHTML = items.length
    ? items.slice(0, 5).map(searchResultCard).join("")
    : emptyState(payload.message || "No markets found.");
}

async function refreshDashboard() {
  const [today, smart, hot, moves] = await Promise.all([
    loadJson("/api/today"),
    loadJson("/api/smart-money/active"),
    loadJson("/api/markets/hot"),
    loadJson("/api/markets/moves"),
  ]);

  renderToday(today);
  renderSmart(smart);
  renderHot(hot);
  renderMoves(moves);
}

function openBot() {
  if (tg && tg.openTelegramLink) {
    tg.openTelegramLink(BOT_URL);
  } else {
    window.open(BOT_URL, "_blank", "noreferrer");
  }
}

document.addEventListener("click", async (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) return;

  if (target.matches("[data-refresh]")) {
    await refreshDashboard();
    return;
  }

  if (target.matches("[data-bot-action]")) {
    openBot();
    return;
  }

  const shareText = target.getAttribute("data-share");
  if (shareText) {
    const text = `${decodeURIComponent(shareText)}\n\nResearch only. No trade execution.\n${BOT_URL}`;
    if (tg && tg.openTelegramLink) {
      tg.openTelegramLink(`https://t.me/share/url?text=${encodeURIComponent(text)}`);
    } else if (navigator.share) {
      await navigator.share({ text });
    } else if (navigator.clipboard) {
      await navigator.clipboard.writeText(text);
      target.textContent = "Copied";
    }
  }
});

document.getElementById("search-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = document.getElementById("search-input").value.trim();
  if (!query) return;
  const target = document.getElementById("search-results");
  target.innerHTML = '<div class="empty-state">Searching markets...</div>';
  const payload = await loadJson(`/api/search?q=${encodeURIComponent(query)}`);
  renderSearch(payload);
});

refreshDashboard();
