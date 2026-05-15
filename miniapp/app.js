const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
const BOT_URL = "https://t.me/PulseMarketAIBot";
const POLYMARKET_URL = "https://polymarket.com";
const EMPTY_MESSAGE = "No data yet. PulseMarket will keep watching.";
const IMPORTANT_MOVE = 5;

const languageCode =
  (tg && tg.initDataUnsafe && tg.initDataUnsafe.user && tg.initDataUnsafe.user.language_code) ||
  navigator.language ||
  "en";
const isRu = String(languageCode).toLowerCase().startsWith("ru");
const lang = isRu ? "ru" : "en";

const copy = {
  en: {
    researchLabel: "Research only · No trade execution",
    botLink: "Bot",
    tabToday: "Today",
    tabRadar: "Radar",
    tabHot: "Hot",
    tabSearch: "Search",
    tabSaved: "Saved",
    tabMore: "More",
    todayKicker: "Curated for today",
    todayTitle: "Today’s Pulse",
    todaySubtitle: "Markets worth watching today.",
    refresh: "Refresh",
    radarKicker: "Public attention",
    radarTitle: "Activity Radar",
    radarSubtitle: "Where public attention is rising.",
    intelligenceLabel: "Intelligence",
    hotKicker: "Secondary scan",
    hotTitle: "Hot Markets",
    hotSubtitle: "Markets with strong current activity.",
    swipeLabel: "Swipe",
    movesKicker: "Only meaningful moves",
    movesTitle: "Sharp Moves",
    movesSubtitle: "Markets where probability changed.",
    searchKicker: "Quick access",
    searchTitle: "Search",
    searchSubtitle: "Find a market and get a simple read.",
    searchPlaceholder: "Search markets, topics, names...",
    searchButton: "Search",
    searchEmpty: "Search markets, topics, names...",
    savedKicker: "Saved markets",
    savedTitle: "Saved markets",
    savedSubtitle: "Save markets to return later.",
    savedEmptyTitle: "No saved markets yet.",
    savedEmptyCopy: "Add markets from the bot.",
    openBot: "Open bot",
    footerSafety: "Research only · No trading · No wallets · No deposits · No private keys · No financial advice",
    footerCopy: "PulseMarket AI helps users understand public market data. It does not execute trades.",
    mainStory: "Main story today",
    probability: "Probability",
    pulseScore: "Pulse Score",
    whyItMatters: "Why it matters",
    exploreMarket: "Explore Market",
    open: "Open",
    publicActivity: "Public activity",
    radarEmpty: "No strong public activity detected right now. PulseMarket will keep watching.",
    radarReason: "Public attention is rising.",
    todayEmpty: "PulseMarket is preparing today’s intelligence.",
    hotEmpty: "No hot markets available yet.",
    movesEmpty: "Sharp Moves\nNo strong move yet.",
    searchLoading: "Searching markets...",
    searchNoResults: "No markets found.",
    veryLow: "Very low probability",
    marketAttentionRising: "Market attention is rising.",
    worthWatching: "Worth watching today.",
    activeToday: "This market is active today.",
    selectedToday: "Selected for today’s market scan.",
    shareCopied: "Copied",
  },
  ru: {
    researchLabel: "Для анализа · Без сделок",
    botLink: "Бот",
    tabToday: "Сегодня",
    tabRadar: "Радар",
    tabHot: "Горячие",
    tabSearch: "Поиск",
    tabSaved: "Сохранённые",
    tabMore: "Ещё",
    todayKicker: "Отобрано на сегодня",
    todayTitle: "Пульс дня",
    todaySubtitle: "Рынки, за которыми сегодня стоит следить.",
    refresh: "Обновить",
    radarKicker: "Публичное внимание",
    radarTitle: "Радар активности",
    radarSubtitle: "Где растёт публичное внимание.",
    intelligenceLabel: "Аналитика",
    hotKicker: "Быстрый обзор",
    hotTitle: "Горячие рынки",
    hotSubtitle: "Рынки с высокой текущей активностью.",
    swipeLabel: "Свайп",
    movesKicker: "Только заметные движения",
    movesTitle: "Резкие движения",
    movesSubtitle: "Рынки, где изменилась вероятность.",
    searchKicker: "Быстрый доступ",
    searchTitle: "Поиск",
    searchSubtitle: "Найди рынок и получи простой смысл.",
    searchPlaceholder: "Ищи рынки, темы, имена...",
    searchButton: "Найти",
    searchEmpty: "Ищи рынки, темы, имена...",
    savedKicker: "Сохранённые рынки",
    savedTitle: "Сохранённые рынки",
    savedSubtitle: "Сохраняй рынки, чтобы вернуться позже.",
    savedEmptyTitle: "Сохранённых рынков пока нет.",
    savedEmptyCopy: "Добавь рынки из бота.",
    openBot: "Открыть бот",
    footerSafety: "Для анализа · Без торговли · Без кошельков · Без пополнений · Без private keys · Без финансовых советов",
    footerCopy: "PulseMarket AI помогает понимать публичные данные рынков. Бот не выполняет сделки.",
    mainStory: "Главное сегодня",
    probability: "Вероятность",
    pulseScore: "Pulse Score",
    whyItMatters: "Почему это важно",
    exploreMarket: "Открыть рынок",
    open: "Открыть",
    publicActivity: "Публичная активность",
    radarEmpty: "Сейчас нет сильной публичной активности. PulseMarket продолжит отслеживание.",
    radarReason: "Публичное внимание растёт.",
    todayEmpty: "PulseMarket готовит обзор на сегодня.",
    hotEmpty: "Пока нет горячих рынков.",
    movesEmpty: "Резкие движения\nСильных движений пока нет.",
    searchLoading: "Ищу рынки...",
    searchNoResults: "Рынки не найдены.",
    veryLow: "Очень низкая вероятность",
    marketAttentionRising: "Внимание к рынку растёт.",
    worthWatching: "Сегодня стоит изучить.",
    activeToday: "Рынок сегодня активен.",
    selectedToday: "Отобран для короткого обзора.",
    shareCopied: "Скопировано",
  },
};

function t(key) {
  return copy[lang][key] || copy.en[key] || key;
}

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

function applyCopy() {
  document.documentElement.lang = lang;
  for (const node of document.querySelectorAll("[data-i18n]")) {
    node.textContent = t(node.getAttribute("data-i18n"));
  }
  for (const node of document.querySelectorAll("[data-i18n-placeholder]")) {
    node.setAttribute("placeholder", t(node.getAttribute("data-i18n-placeholder")));
  }
}

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
  const number = Number(value);
  if (number <= 0) return t("veryLow");
  if (number < 1) return "<1%";
  return `${Math.round(number)}%`;
}

function probability(item) {
  if (item && item.probability !== null && item.probability !== undefined) {
    return percent(item.probability);
  }
  if (item && item.probability_label) return item.probability_label;
  return percent(null);
}

function movement(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "n/a";
  const rounded = Math.round(Number(value));
  const prefix = rounded > 0 ? "+" : "";
  return `${prefix}${rounded}%`;
}

function hasImportantMove(value) {
  return value !== null && value !== undefined && Math.abs(Number(value)) >= IMPORTANT_MOVE;
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

function emptyState(message, compact = false) {
  return `<div class="empty-state${compact ? " empty-state--compact" : ""}">${escapeHtml(message || EMPTY_MESSAGE).replaceAll("\n", "<br>")}</div>`;
}

function shortReason(item) {
  if (!isRu && item && item.why_it_matters) {
    const sentence = String(item.why_it_matters).split(".")[0].trim();
    return sentence ? `${sentence}.` : t("selectedToday");
  }
  if (item && hasImportantMove(item.movement)) return t("marketAttentionRising");
  if (Number((item && item.pulse_score) || 0) >= 70) return t("worthWatching");
  if (Number((item && item.volume) || 0) >= 100000) return t("activeToday");
  return t("selectedToday");
}

function openLink(url) {
  const safe = escapeHtml(safeUrl(url));
  return `<a href="${safe}" target="_blank" rel="noreferrer">${escapeHtml(t("open"))}</a>`;
}

function actionLink(item, label = t("open")) {
  const safe = escapeHtml(safeUrl(item && item.url));
  return `
    <div class="market-actions">
      <a class="market-action market-action--primary" href="${safe}" target="_blank" rel="noreferrer">${escapeHtml(label)}</a>
    </div>
  `;
}

function marketSummaryCard(item) {
  const importantMoveBadge = hasImportantMove(item.movement)
    ? `<span class="badge">Move ${movement(item.movement)}</span>`
    : "";
  return `
    <article class="market-card compact-market-card">
      <h3 class="card-title">${escapeHtml(item.title || "Untitled market")}</h3>
      <div class="small-meta">
        <span class="badge badge--accent">${probability(item)}</span>
        <span class="badge badge--blue">Pulse ${escapeHtml(item.pulse_score ?? 0)}/100</span>
        ${importantMoveBadge}
      </div>
      <p class="why-copy why-copy--short">${escapeHtml(shortReason(item))}</p>
      <div class="card-link-row">
        ${openLink(item.url)}
      </div>
    </article>
  `;
}

function searchResultCard(item) {
  return `
    <article class="search-card compact-market-card">
      <h3 class="card-title">${escapeHtml(item.title || "Untitled market")}</h3>
      <div class="small-meta">
        <span class="badge badge--accent">${probability(item)}</span>
        <span class="badge badge--blue">Pulse ${escapeHtml(item.pulse_score ?? 0)}/100</span>
      </div>
      <p class="why-copy why-copy--short">${escapeHtml(shortReason(item))}</p>
      <div class="card-link-row">
        ${openLink(item.url)}
      </div>
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
    hero.innerHTML = emptyState(t("todayEmpty"));
    return;
  }

  const top = items[0];
  hero.innerHTML = `
    <div>
      <p class="section-kicker">${escapeHtml(t("mainStory"))}</p>
      <h3 class="story-title">${escapeHtml(top.title || "Untitled market")}</h3>
    </div>
    <div class="hero-meta">
      <span class="badge badge--accent">${escapeHtml(t("probability"))}: ${probability(top)}</span>
      <span class="badge badge--blue">${escapeHtml(t("pulseScore"))}: ${escapeHtml(top.pulse_score ?? 0)}/100</span>
    </div>
    <p class="why-copy"><span class="why-label">${escapeHtml(t("whyItMatters"))}</span>${escapeHtml(shortReason(top))}</p>
    ${actionLink(top, t("exploreMarket"))}
  `;

  secondary.innerHTML = items.slice(1, 3).map((item) => marketSummaryCard(item)).join("");
}

function renderSmart(payload) {
  const hero = document.getElementById("smart-hero");
  const items = dataFrom(payload);
  clearNode(hero);

  if (!items.length) {
    hero.innerHTML = emptyState(t("radarEmpty"), true);
    return;
  }

  const item = items[0];
  hero.innerHTML = `
    <div>
      <p class="section-kicker">${escapeHtml(t("radarTitle"))}</p>
      <h3 class="story-title">${escapeHtml(item.title || "Public market activity")}</h3>
    </div>
    <div class="hero-meta">
      <span class="badge badge--accent">${escapeHtml(t("publicActivity"))}: ${compactUsd(item.public_activity)}</span>
    </div>
    <p class="why-copy"><span class="why-label">${escapeHtml(t("whyItMatters"))}</span>${escapeHtml(t("radarReason"))}</p>
    <p class="micro-note">${escapeHtml(t("researchLabel"))}</p>
    <div class="card-link-row">
      ${openLink(item.url)}
    </div>
  `;
}

function renderHot(payload) {
  const target = document.getElementById("hot-strip");
  const items = dataFrom(payload);
  target.innerHTML = items.length
    ? items.slice(0, 5).map((item) => marketSummaryCard(item)).join("")
    : emptyState(payload.message || t("hotEmpty"), true);
}

function renderMoves(payload) {
  const target = document.getElementById("moves-list");
  const items = dataFrom(payload).filter((item) => hasImportantMove(item.movement));
  if (!items.length) {
    target.innerHTML = emptyState(t("movesEmpty"), true);
    return;
  }

  target.innerHTML = items
    .slice(0, 4)
    .map(
      (item) => `
        <article class="move-card">
          <div>
            <h3 class="card-title">${escapeHtml(item.title || "Untitled market")}</h3>
            <div class="small-meta">
              <span class="badge badge--accent">${probability(item)}</span>
              <span class="badge badge--blue">Pulse ${escapeHtml(item.pulse_score ?? 0)}/100</span>
            </div>
            <div class="card-link-row">
              ${openLink(item.url)}
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
    : emptyState(payload.message || t("searchNoResults"), true);
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

function scrollToSection(sectionId) {
  const section = document.getElementById(sectionId);
  if (section) {
    section.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function setActiveSection(sectionId) {
  const activeId = sectionId === "more" ? "moves" : sectionId;
  for (const button of document.querySelectorAll("[data-nav-target]")) {
    button.classList.toggle("is-active", button.getAttribute("data-nav-target") === activeId);
  }
}

function setupNavigation() {
  document.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    const navButton = target.closest("[data-nav-target]");
    if (!(navButton instanceof HTMLElement)) return;
    const sectionId = navButton.getAttribute("data-nav-target");
    if (sectionId) {
      setActiveSection(sectionId);
      scrollToSection(sectionId);
    }
  });

  if (!("IntersectionObserver" in window)) return;
  const observer = new IntersectionObserver(
    (entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (visible && visible.target.id) {
        setActiveSection(visible.target.id);
      }
    },
    { rootMargin: "-28% 0px -58% 0px", threshold: [0.14, 0.28, 0.42] },
  );
  for (const section of document.querySelectorAll("[data-section]")) {
    observer.observe(section);
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
    const text = `${decodeURIComponent(shareText)}\n\n${t("researchLabel")}\n${BOT_URL}`;
    if (tg && tg.openTelegramLink) {
      tg.openTelegramLink(`https://t.me/share/url?text=${encodeURIComponent(text)}`);
    } else if (navigator.share) {
      await navigator.share({ text });
    } else if (navigator.clipboard) {
      await navigator.clipboard.writeText(text);
      target.textContent = t("shareCopied");
    }
  }
});

document.getElementById("search-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = document.getElementById("search-input").value.trim();
  if (!query) return;
  const target = document.getElementById("search-results");
  target.innerHTML = emptyState(t("searchLoading"), true);
  const payload = await loadJson(`/api/search?q=${encodeURIComponent(query)}`);
  renderSearch(payload);
});

applyCopy();
setupNavigation();
refreshDashboard();
