const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;

if (tg) {
  tg.ready();
  tg.expand();
  document.documentElement.style.setProperty(
    "--bg",
    tg.themeParams.bg_color || "#061019",
  );
}

const money = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

function compactUsd(value) {
  if (value === null || value === undefined) return "n/a";
  const abs = Math.abs(Number(value));
  if (abs >= 1_000_000) return `$${(Number(value) / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `$${(Number(value) / 1_000).toFixed(0)}K`;
  return money.format(Number(value));
}

function percent(value) {
  if (value === null || value === undefined) return "n/a";
  return `${value}%`;
}

function movement(value) {
  if (value === null || value === undefined) return "n/a";
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value}%`;
}

async function loadJson(path) {
  try {
    const response = await fetch(path, { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    return { data: [], message: "No data yet. PulseMarket will keep watching." };
  }
}

function emptyState(message) {
  const div = document.createElement("div");
  div.className = "empty";
  div.textContent = message || "No data yet. PulseMarket will keep watching.";
  return div;
}

function marketCard(item) {
  const article = document.createElement("article");
  article.className = "market-card";

  const risks = Array.isArray(item.risk_flags) && item.risk_flags.length
    ? `<ul class="risk-list">${item.risk_flags.map((flag) => `<li>${flag}</li>`).join("")}</ul>`
    : "";

  article.innerHTML = `
    <h3>${item.title || "Untitled market"}</h3>
    <div class="market-meta">
      <span class="badge badge--green">Probability: ${percent(item.probability)}</span>
      <span class="badge">Movement: ${movement(item.movement)}</span>
      <span class="badge">Volume: ${compactUsd(item.volume)}</span>
    </div>
    <div class="score-row">
      <span>Pulse ${item.pulse_score ?? 0}/100</span>
      <span>Health ${item.market_health_score ?? 0}/100</span>
    </div>
    ${item.why_it_matters ? `<p class="why">${item.why_it_matters}</p>` : ""}
    ${risks}
    <div class="actions">
      <a href="${item.url || "https://polymarket.com"}" target="_blank" rel="noreferrer">Open Polymarket</a>
      <button type="button" data-share="${encodeURIComponent(item.title || "PulseMarket AI")}">Share text</button>
    </div>
  `;
  return article;
}

function smartCard(item) {
  const article = document.createElement("article");
  article.className = "market-card";
  article.innerHTML = `
    <h3>${item.title || "Public market activity"}</h3>
    <div class="market-meta">
      <span class="badge badge--green">Public activity: ${compactUsd(item.public_activity)}</span>
      <span class="badge">Public trades: ${item.trades_count ?? "n/a"}</span>
    </div>
    <p class="why">
      Public activity is above the visibility threshold. Use it as research context.
    </p>
    <div class="actions">
      <a href="${item.url || "https://polymarket.com"}" target="_blank" rel="noreferrer">Open Polymarket</a>
    </div>
  `;
  return article;
}

function renderList(targetId, payload, renderer) {
  const target = document.getElementById(targetId);
  target.innerHTML = "";
  const data = Array.isArray(payload.data) ? payload.data : [];
  if (!data.length) {
    target.appendChild(emptyState(payload.message));
    return;
  }
  data.slice(0, 5).forEach((item) => target.appendChild(renderer(item)));
}

async function refreshDashboard() {
  const [today, smart, hot, moves] = await Promise.all([
    loadJson("/api/today"),
    loadJson("/api/smart-money/active"),
    loadJson("/api/markets/hot"),
    loadJson("/api/markets/moves"),
  ]);

  renderList("today", today, marketCard);
  renderList("smart", smart, smartCard);
  renderList("hot", hot, marketCard);
  renderList("moves", moves, marketCard);
}

document.addEventListener("click", async (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) return;

  if (target.matches("[data-refresh]")) {
    await refreshDashboard();
  }

  const shareText = target.getAttribute("data-share");
  if (shareText) {
    const text = `${decodeURIComponent(shareText)}\n\nResearch only. No trade execution.\nhttps://t.me/PulseMarketAIBot`;
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
  const payload = await loadJson(`/api/search?q=${encodeURIComponent(query)}`);
  renderList("search-results", payload, marketCard);
});

refreshDashboard();
