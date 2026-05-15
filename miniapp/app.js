const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
const BOT_URL = "https://t.me/PulseMarketAIBot";
const APP_URL = "https://app.pulsemarketai.com/app";
const POLYMARKET_URL = "https://polymarket.com";
const EMPTY_MESSAGE = "No data yet. PulseMarket will keep watching.";
const STORAGE_PREFIX = "pulsemarket-miniapp:";
const SEARCH_SUGGESTIONS = ["bitcoin", "election", "fed", "ai", "sports"];

const browserLanguage =
  (tg && tg.initDataUnsafe && tg.initDataUnsafe.user && tg.initDataUnsafe.user.language_code) ||
  navigator.language ||
  "en";

const state = {
  activeTab: "today",
  languageSetting: readStorage("language", "auto"),
  themeSetting: readStorage("theme", "system"),
  toggles: readJsonStorage("toggles", {
    todayNotifications: false,
    activityNotifications: false,
    sharpMoveNotifications: false,
    compactMode: false,
    reducedAnimations: false,
  }),
  today: [],
  radar: [],
  hot: [],
  moves: [],
  searchResults: [],
};

const copy = {
  en: {
    productLine: "Understand what matters on Polymarket.",
    researchLabel: "Research only · No trade execution",
    botLink: "Bot",
    refresh: "Refresh",
    todayTab: "Today",
    radarTab: "Radar",
    searchTab: "Search",
    savedTab: "Saved",
    moreTab: "More",
    todayContext: "Markets worth watching today.",
    radarContext: "Where public attention is rising.",
    searchContext: "Find markets fast.",
    savedContext: "Markets to return to later.",
    moreContext: "Settings and product links.",
    mainReason: "Daily briefing",
    todayTitle: "Morning Briefing",
    todaySubtitle: "Your quick read of what matters today.",
    shareSnapshot: "Share briefing",
    attentionLayer: "Attention layer",
    radarTitle: "Activity Radar",
    radarSubtitle: "Markets where public attention is rising.",
    spotlight: "Spotlight search",
    searchTitle: "Search",
    searchSubtitle: "Find a market and get a simple read.",
    searchPlaceholder: "Search markets, topics, names...",
    searchButton: "Search",
    searchEmpty: "Search like Spotlight. Try bitcoin, election, fed, AI.",
    trendingSearches: "Trending searches",
    recentSearches: "Recent searches",
    returnLater: "Return later",
    savedTitle: "Saved markets",
    savedSubtitle: "Keep markets you want to revisit.",
    recentlyOpened: "Recently opened",
    localOnly: "Stored on this device",
    controls: "Controls",
    moreTitle: "More",
    moreSubtitle: "Tune the app and learn what the signals mean.",
    language: "Language",
    languageHint: "Use Telegram language or choose manually.",
    theme: "Theme",
    themeHint: "Clean light mode or focused dark mode.",
    todayNotifications: "Morning Briefing notifications",
    activityNotifications: "Activity alerts",
    sharpMoveNotifications: "Sharp move alerts",
    compactMode: "Compact mode",
    reducedAnimations: "Reduced animations",
    whatPulse: "What is Pulse Score?",
    pulseMeaning: "How interesting this market looks today.",
    whatRadar: "What is Activity Radar?",
    radarMeaning: "It shows where public attention is increasing.",
    whatMood: "What is Market Mood?",
    moodMeaning: "A plain-language read of how active a market feels.",
    channel: "Channel",
    support: "Support",
    shareApp: "Share app",
    feedback: "Send feedback",
    footerSafety: "Research only · No trading · No wallets · No deposits · No private keys · No financial advice",
    footerCopy: "PulseMarket AI helps users understand public market data. It does not execute trades.",
    mainStory: "Main story",
    secondaryStories: "Also worth a look",
    probability: "Probability",
    pulseScore: "Pulse Score",
    whyItMatters: "Why people care",
    whyPeopleCare: "Why people care",
    watchNext: "Watch",
    watchNextCopy: "Probability, activity, and resolution rules.",
    marketMood: "Market Mood",
    exploreMarket: "Explore Market",
    open: "Open",
    save: "Save",
    saved: "Saved",
    remove: "Remove",
    share: "Share",
    publicActivity: "Public activity",
    activityLevel: "Activity level",
    radarEmpty: "No strong public activity detected right now. PulseMarket will keep watching.",
    radarReason: "Attention is rising around this market.",
    radarListTitle: "More markets getting attention",
    todayEmpty: "PulseMarket is preparing today’s intelligence.",
    hotTitle: "Hot markets",
    hotSubtitle: "Markets with strong current activity.",
    hotEmpty: "No hot markets available yet.",
    movesTitle: "Sharp moves",
    movesSubtitle: "Markets where probability changed.",
    movesEmpty: "No strong move yet.",
    savedEmptyTitle: "No saved markets yet.",
    savedEmptyCopy: "Save markets from Today, Radar, Hot, or Search.",
    recentEmpty: "No opened markets yet.",
    searchLoading: "Searching markets...",
    searchNoResults: "No markets found.",
    veryLow: "Very low probability",
    lowButActive: "Low probability, but this market may still be active.",
    marketAttentionRising: "People are paying more attention to this market.",
    worthWatching: "Worth watching today.",
    activeToday: "People are watching this because activity increased.",
    selectedToday: "Selected for today’s market scan.",
    simpleReadTitle: "Simple Read",
    simpleReadCopy: "This market asks whether an event will happen. Watch the probability and rules before drawing conclusions.",
    moodQuiet: "Quiet",
    moodActive: "Active",
    moodHeating: "Heating up",
    moodVolatile: "Volatile",
    moodEnding: "Ending soon",
    copied: "Copied",
    appShared: "PulseMarket AI helps you understand what matters on Polymarket.",
  },
  ru: {
    productLine: "Быстро понять, что важно на Polymarket.",
    researchLabel: "Для анализа · Без сделок",
    botLink: "Бот",
    refresh: "Обновить",
    todayTab: "Сегодня",
    radarTab: "Радар",
    searchTab: "Поиск",
    savedTab: "Сохранённые",
    moreTab: "Ещё",
    todayContext: "Рынки, за которыми сегодня стоит следить.",
    radarContext: "Где растёт публичное внимание.",
    searchContext: "Быстро найти рынок.",
    savedContext: "Рынки, к которым можно вернуться.",
    moreContext: "Настройки и ссылки продукта.",
    mainReason: "Утренний обзор",
    todayTitle: "Пульс дня",
    todaySubtitle: "Короткая картина дня.",
    shareSnapshot: "Поделиться обзором",
    attentionLayer: "Слой внимания",
    radarTitle: "Радар активности",
    radarSubtitle: "Рынки, где растёт публичное внимание.",
    spotlight: "Быстрый поиск",
    searchTitle: "Поиск",
    searchSubtitle: "Найди рынок и получи простой смысл.",
    searchPlaceholder: "Ищи рынки, темы, имена...",
    searchButton: "Найти",
    searchEmpty: "Поиск как Spotlight. Попробуй bitcoin, election, fed, AI.",
    trendingSearches: "Популярные запросы",
    recentSearches: "Недавние запросы",
    returnLater: "Вернуться позже",
    savedTitle: "Сохранённые рынки",
    savedSubtitle: "Сохраняй рынки, к которым хочешь вернуться.",
    recentlyOpened: "Недавно открытые",
    localOnly: "Сохранено на этом устройстве",
    controls: "Управление",
    moreTitle: "Ещё",
    moreSubtitle: "Настройки и объяснение сигналов.",
    language: "Язык",
    languageHint: "Авто по Telegram или выбор вручную.",
    theme: "Тема",
    themeHint: "Светлый режим или сфокусированный тёмный.",
    todayNotifications: "Уведомления Пульса дня",
    activityNotifications: "Уведомления активности",
    sharpMoveNotifications: "Уведомления о движениях",
    compactMode: "Компактный режим",
    reducedAnimations: "Меньше анимаций",
    whatPulse: "Что такое Pulse Score?",
    pulseMeaning: "Насколько рынок сейчас интересен.",
    whatRadar: "Что такое Радар активности?",
    radarMeaning: "Показывает, где растёт публичное внимание.",
    whatMood: "Что такое Market Mood?",
    moodMeaning: "Простая оценка того, насколько рынок сейчас активен.",
    channel: "Канал",
    support: "Поддержка",
    shareApp: "Поделиться",
    feedback: "Отзыв",
    footerSafety: "Для анализа · Без торговли · Без кошельков · Без пополнений · Без private keys · Без финансовых советов",
    footerCopy: "PulseMarket AI помогает понимать публичные данные рынков. Бот не выполняет сделки.",
    mainStory: "Главное",
    secondaryStories: "Ещё стоит посмотреть",
    probability: "Вероятность",
    pulseScore: "Pulse Score",
    whyItMatters: "Почему это важно",
    whyPeopleCare: "Почему людям это интересно",
    watchNext: "За чем следить",
    watchNextCopy: "Вероятность, активность и правила разрешения.",
    marketMood: "Настроение рынка",
    exploreMarket: "Открыть рынок",
    open: "Открыть",
    save: "Сохранить",
    saved: "Сохранено",
    remove: "Удалить",
    share: "Поделиться",
    publicActivity: "Публичная активность",
    activityLevel: "Уровень активности",
    radarEmpty: "Сейчас нет сильной публичной активности. PulseMarket продолжит отслеживание.",
    radarReason: "Внимание к этому рынку растёт.",
    radarListTitle: "Ещё рынки с ростом внимания",
    todayEmpty: "PulseMarket готовит обзор на сегодня.",
    hotTitle: "Горячие рынки",
    hotSubtitle: "Рынки с сильной текущей активностью.",
    hotEmpty: "Пока нет горячих рынков.",
    movesTitle: "Резкие движения",
    movesSubtitle: "Рынки, где изменилась вероятность.",
    movesEmpty: "Сильных движений пока нет.",
    savedEmptyTitle: "Сохранённых рынков пока нет.",
    savedEmptyCopy: "Сохраняй рынки из Сегодня, Радара, Горячих или Поиска.",
    recentEmpty: "Открытых рынков пока нет.",
    searchLoading: "Ищу рынки...",
    searchNoResults: "Рынки не найдены.",
    veryLow: "Очень низкая вероятность",
    lowButActive: "Вероятность низкая, но рынок может быть активным.",
    marketAttentionRising: "К этому рынку растёт внимание.",
    worthWatching: "Сегодня стоит изучить.",
    activeToday: "За этим следят, потому что активность выросла.",
    selectedToday: "Отобран для короткого обзора.",
    simpleReadTitle: "Простой смысл",
    simpleReadCopy: "Этот рынок спрашивает, произойдёт ли событие. Смотри на вероятность и правила разрешения, прежде чем делать выводы.",
    moodQuiet: "Тихо",
    moodActive: "Активно",
    moodHeating: "Разогревается",
    moodVolatile: "Волатильно",
    moodEnding: "Скоро завершение",
    copied: "Скопировано",
    appShared: "PulseMarket AI помогает быстро понять, что важно на Polymarket.",
  },
};

function readStorage(key, fallback) {
  try {
    return localStorage.getItem(`${STORAGE_PREFIX}${key}`) || fallback;
  } catch {
    return fallback;
  }
}

function writeStorage(key, value) {
  try {
    localStorage.setItem(`${STORAGE_PREFIX}${key}`, value);
  } catch {
    // Local storage can be disabled inside some embedded browsers.
  }
}

function readJsonStorage(key, fallback) {
  try {
    const value = localStorage.getItem(`${STORAGE_PREFIX}${key}`);
    return value ? JSON.parse(value) : fallback;
  } catch {
    return fallback;
  }
}

function writeJsonStorage(key, value) {
  writeStorage(key, JSON.stringify(value));
}

function currentLanguage() {
  if (state.languageSetting === "en" || state.languageSetting === "ru") return state.languageSetting;
  return String(browserLanguage).toLowerCase().startsWith("ru") ? "ru" : "en";
}

function t(key) {
  const language = currentLanguage();
  return copy[language][key] || copy.en[key] || key;
}

function isRu() {
  return currentLanguage() === "ru";
}

if (tg) {
  tg.ready();
  tg.expand();
  if (tg.BackButton) tg.BackButton.hide();
}

const money = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

function applyTheme() {
  const preferredLight = window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches;
  const theme =
    state.themeSetting === "system" ? (preferredLight ? "light" : "dark") : state.themeSetting;
  document.documentElement.dataset.theme = theme;
  document.documentElement.dataset.compact = state.toggles.compactMode ? "true" : "false";
  document.documentElement.dataset.reducedMotion = state.toggles.reducedAnimations ? "true" : "false";
}

function applyCopy() {
  const language = currentLanguage();
  document.documentElement.lang = language;
  for (const node of document.querySelectorAll("[data-i18n]")) {
    node.textContent = t(node.getAttribute("data-i18n"));
  }
  for (const node of document.querySelectorAll("[data-i18n-placeholder]")) {
    node.setAttribute("placeholder", t(node.getAttribute("data-i18n-placeholder")));
  }
  updateContext();
  updateSettingsControls();
}

function updateSettingsControls() {
  for (const button of document.querySelectorAll("[data-setting='language']")) {
    button.classList.toggle("is-selected", button.dataset.value === state.languageSetting);
  }
  for (const button of document.querySelectorAll("[data-setting='theme']")) {
    button.classList.toggle("is-selected", button.dataset.value === state.themeSetting);
  }
  for (const button of document.querySelectorAll("[data-toggle]")) {
    const key = button.dataset.toggle;
    const enabled = Boolean(state.toggles[key]);
    button.classList.toggle("is-on", enabled);
    button.setAttribute("aria-pressed", String(enabled));
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

function marketId(item) {
  return String((item && (item.market_id || item.id || item.url || item.title)) || "unknown");
}

function dataFrom(payload) {
  return Array.isArray(payload && payload.data) ? payload.data : [];
}

async function loadJson(path) {
  try {
    const response = await fetch(path, { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch {
    return { data: [], message: EMPTY_MESSAGE };
  }
}

function clearNode(node) {
  node.classList.remove("skeleton-card");
  node.innerHTML = "";
}

function emptyState(message, compact = false) {
  return `<div class="empty-state${compact ? " empty-state--compact" : ""}">${escapeHtml(message || EMPTY_MESSAGE)}</div>`;
}

function shortReason(item) {
  if (!isRu() && item && item.why_it_matters) {
    const sentence = String(item.why_it_matters).split(".")[0].trim();
    return sentence ? `${sentence}.` : t("selectedToday");
  }
  if (item && Number(item.probability) > 0 && Number(item.probability) < 1) return t("lowButActive");
  if (item && Number(item.public_activity || 0) > 0) return t("marketAttentionRising");
  if (Number((item && item.pulse_score) || 0) >= 70) return t("worthWatching");
  if (Number((item && item.volume) || 0) >= 100000) return t("activeToday");
  return t("selectedToday");
}

function marketMood(item) {
  const key = item && item.market_mood ? String(item.market_mood) : inferMoodKey(item || {});
  const labels = {
    quiet: t("moodQuiet"),
    active: t("moodActive"),
    heating_up: t("moodHeating"),
    volatile: t("moodVolatile"),
    ending_soon: t("moodEnding"),
  };
  return {
    key,
    label: labels[key] || labels.quiet,
    reason: !isRu() && item && item.market_mood_reason ? item.market_mood_reason : moodReason(key),
  };
}

function inferMoodKey(item) {
  const movement = Math.abs(Number(item.movement || 0));
  const volume = Number(item.volume || item.public_activity || 0);
  const endDate = item.end_date ? new Date(item.end_date).getTime() : null;
  const hoursLeft = endDate ? (endDate - Date.now()) / 36e5 : null;
  if (hoursLeft !== null && hoursLeft <= 24) return "ending_soon";
  if (movement >= 10) return "volatile";
  if (movement >= 5 || volume >= 500000) return "heating_up";
  if (volume >= 100000 || Number(item.public_activity || 0) > 0) return "active";
  return "quiet";
}

function moodReason(key) {
  if (isRu()) {
    return {
      quiet: "Сильного движения пока нет.",
      active: "За этим следят, потому что активность уже есть.",
      heating_up: "Внимание к этому рынку растёт.",
      volatile: "Вероятность заметно изменилась, поэтому рынок выделяется.",
      ending_soon: "Рынок близок к разрешению.",
    }[key] || "Сильного движения пока нет.";
  }
  return {
    quiet: "No strong movement yet.",
    active: "People are watching this because activity is present.",
    heating_up: "Attention is rising around this market.",
    volatile: "Probability moved enough to make the market noticeable.",
    ending_soon: "The market is close to resolution.",
  }[key] || "No strong movement yet.";
}

function savedMarkets() {
  return readJsonStorage("savedMarkets", []);
}

function recentlyOpened() {
  return readJsonStorage("recentlyOpened", []);
}

function recentSearches() {
  return readJsonStorage("recentSearches", []);
}

function saveRecentSearch(query) {
  const normalized = query.trim();
  if (!normalized) return;
  const next = [normalized, ...recentSearches().filter((item) => item.toLowerCase() !== normalized.toLowerCase())].slice(0, 5);
  writeJsonStorage("recentSearches", next);
  renderSearchSuggestions();
}

function addRecentMarket(item) {
  const normalized = normalizeMarket(item);
  const next = [normalized, ...recentlyOpened().filter((saved) => saved.id !== normalized.id)].slice(0, 5);
  writeJsonStorage("recentlyOpened", next);
  renderSaved();
}

function normalizeMarket(item) {
  const mood = marketMood(item || {});
  return {
    id: marketId(item),
    title: item && item.title ? item.title : "Untitled market",
    url: safeUrl(item && item.url),
    probability: item && item.probability,
    pulse_score: item && item.pulse_score,
    why: shortReason(item || {}),
    market_mood: mood.key,
    market_mood_label: mood.label,
    market_mood_reason: mood.reason,
  };
}

function isSaved(item) {
  const id = typeof item === "string" ? item : marketId(item);
  return savedMarkets().some((saved) => saved.id === id);
}

function saveMarket(item) {
  const normalized = normalizeMarket(item);
  if (!isSaved(normalized.id)) {
    writeJsonStorage("savedMarkets", [normalized, ...savedMarkets()].slice(0, 24));
  }
  renderAllSavedButtons();
  renderSaved();
}

function removeSaved(id) {
  writeJsonStorage("savedMarkets", savedMarkets().filter((item) => item.id !== id));
  renderAllSavedButtons();
  renderSaved();
}

function marketText(item) {
  const mood = marketMood(item);
  return `${item.title || "Polymarket market"}\n${t("probability")}: ${probability(item)}\n${t("marketMood")}: ${mood.label}\n${t("pulseScore")}: ${item.pulse_score ?? 0}/100\n${t("whyPeopleCare")}: ${shortReason(item)}\n${safeUrl(item.url)}`;
}

async function shareText(text) {
  const finalText = `${text}\n\n${t("researchLabel")}\n${BOT_URL}`;
  if (tg && tg.openTelegramLink) {
    tg.openTelegramLink(`https://t.me/share/url?text=${encodeURIComponent(finalText)}`);
    return;
  }
  if (navigator.share) {
    await navigator.share({ text: finalText });
    return;
  }
  if (navigator.clipboard) {
    await navigator.clipboard.writeText(finalText);
  }
}

function buttonRow(item) {
  const encoded = encodeURIComponent(JSON.stringify(normalizeMarket(item)));
  const saved = isSaved(item);
  return `
    <div class="action-row">
      <a class="primary-action" href="${escapeHtml(safeUrl(item && item.url))}" target="_blank" rel="noreferrer" data-open-market="${encoded}">${escapeHtml(t("open"))}</a>
      <button type="button" class="soft-action" data-save-market="${encoded}">${escapeHtml(saved ? t("saved") : t("save"))}</button>
      <button type="button" class="soft-action" data-share-market="${encoded}">${escapeHtml(t("share"))}</button>
    </div>
  `;
}

function marketCard(item, variant = "compact") {
  const mood = marketMood(item);
  return `
    <article class="market-card market-card--${variant}">
      <div class="market-card__main">
        <h3>${escapeHtml(item.title || "Untitled market")}</h3>
        <p><strong>${escapeHtml(t("whyPeopleCare"))}:</strong> ${escapeHtml(shortReason(item))}</p>
      </div>
      <div class="pill-row">
        <span class="pill pill--prob">${escapeHtml(probability(item))}</span>
        <span class="pill pill--mood">${escapeHtml(mood.label)}</span>
        <span class="pill pill--pulse">Pulse ${escapeHtml(item.pulse_score ?? 0)}/100</span>
      </div>
      <p class="simple-read"><strong>${escapeHtml(t("simpleReadTitle"))}:</strong> ${escapeHtml(t("simpleReadCopy"))}</p>
      ${buttonRow(item)}
    </article>
  `;
}

function savedCard(item, removable = false) {
  const encoded = encodeURIComponent(JSON.stringify(item));
  const mood = marketMood(item);
  return `
    <article class="market-card market-card--saved">
      <div class="market-card__main">
        <h3>${escapeHtml(item.title || "Untitled market")}</h3>
        <p>${escapeHtml(item.why || t("selectedToday"))}</p>
      </div>
      <div class="pill-row">
        <span class="pill pill--prob">${escapeHtml(percent(item.probability))}</span>
        <span class="pill pill--mood">${escapeHtml(mood.label)}</span>
        <span class="pill pill--pulse">Pulse ${escapeHtml(item.pulse_score ?? 0)}/100</span>
      </div>
      <div class="action-row">
        <a class="primary-action" href="${escapeHtml(safeUrl(item.url))}" target="_blank" rel="noreferrer" data-open-market="${encoded}">${escapeHtml(t("open"))}</a>
        ${
          removable
            ? `<button type="button" class="soft-action" data-remove-market="${escapeHtml(item.id)}">${escapeHtml(t("remove"))}</button>`
            : `<button type="button" class="soft-action" data-save-market="${encoded}">${escapeHtml(isSaved(item.id) ? t("saved") : t("save"))}</button>`
        }
      </div>
    </article>
  `;
}

function renderToday(payload) {
  state.today = dataFrom(payload);
  const hero = document.getElementById("today-hero");
  const secondary = document.getElementById("today-secondary");
  clearNode(hero);
  secondary.innerHTML = "";

  if (!state.today.length) {
    hero.innerHTML = emptyState(t("todayEmpty"));
    return;
  }

  const top = state.today[0];
  const topMood = marketMood(top);
  hero.innerHTML = `
    <div class="story-card__topline">
      <span>${escapeHtml(t("mainStory"))}</span>
      <span>${escapeHtml(topMood.label)}</span>
    </div>
    <h3>${escapeHtml(top.title || "Untitled market")}</h3>
    <div class="metric-line">
      <span>${escapeHtml(t("probability"))}</span>
      <strong>${escapeHtml(probability(top))}</strong>
    </div>
    <div class="pill-row">
      <span class="pill pill--pulse">Pulse ${escapeHtml(top.pulse_score ?? 0)}/100</span>
      <span class="pill pill--mood">${escapeHtml(topMood.label)}</span>
    </div>
    <p><strong>${escapeHtml(t("whyPeopleCare"))}:</strong> ${escapeHtml(shortReason(top))}</p>
    <p class="watch-copy"><strong>${escapeHtml(t("watchNext"))}:</strong> ${escapeHtml(t("watchNextCopy"))}</p>
    ${buttonRow(top)}
  `;

  secondary.innerHTML = state.today.slice(1, 4).map((item) => marketCard(item, "secondary")).join("");
}

function renderRadar(payload) {
  state.radar = dataFrom(payload);
  const hero = document.getElementById("smart-hero");
  const list = document.getElementById("radar-list");
  clearNode(hero);
  list.innerHTML = "";

  if (!state.radar.length) {
    hero.innerHTML = emptyState(t("radarEmpty"), true);
    return;
  }

  const top = state.radar[0];
  hero.innerHTML = `
    <div class="story-card__topline">
      <span>${escapeHtml(t("radarTitle"))}</span>
      <span>${escapeHtml(t("activityLevel"))}</span>
    </div>
    <h3>${escapeHtml(top.title || "Public market activity")}</h3>
    <div class="metric-line">
      <span>${escapeHtml(t("publicActivity"))}</span>
      <strong>${compactUsd(top.public_activity)}</strong>
    </div>
    <p><strong>${escapeHtml(t("whyPeopleCare"))}:</strong> ${escapeHtml(top.why_it_matters || t("radarReason"))}</p>
    ${buttonRow({ ...top, pulse_score: top.pulse_score || 0, probability: top.probability })}
  `;

  const rest = state.radar.slice(1, 5);
  if (rest.length) {
    list.innerHTML = `
      <h3 class="list-title">${escapeHtml(t("radarListTitle"))}</h3>
      ${rest
        .map(
          (item) => `
            <article class="activity-row">
              <div>
                <h4>${escapeHtml(item.title || "Public market activity")}</h4>
                <p>${escapeHtml(item.why_it_matters || t("radarReason"))}</p>
              </div>
              <div class="activity-row__side">
                <strong>${compactUsd(item.public_activity)}</strong>
                <a href="${escapeHtml(safeUrl(item.url))}" target="_blank" rel="noreferrer" data-open-market="${encodeURIComponent(
                  JSON.stringify(normalizeMarket(item)),
                )}">${escapeHtml(t("open"))}</a>
              </div>
            </article>
          `,
        )
        .join("")}
    `;
  }
}

function renderHot(payload) {
  state.hot = dataFrom(payload);
}

function renderMoves(payload) {
  state.moves = dataFrom(payload).filter((item) => Math.abs(Number(item.movement || 0)) >= 5);
}

function renderSearch(payload) {
  state.searchResults = dataFrom(payload);
  const target = document.getElementById("search-results");
  target.innerHTML = state.searchResults.length
    ? state.searchResults.slice(0, 5).map((item) => marketCard(item, "search")).join("")
    : emptyState(payload.message || t("searchNoResults"), true);
}

function renderTodayExtras() {
  const todayScreen = document.getElementById("screen-today");
  let existing = document.getElementById("today-extras");
  if (!existing) {
    existing = document.createElement("div");
    existing.id = "today-extras";
    existing.className = "subsection";
    todayScreen.appendChild(existing);
  }

  const hotCards = state.hot.slice(0, 5).map((item) => marketCard(item, "compact")).join("");
  const movesCards = state.moves.slice(0, 3).map((item) => marketCard(item, "compact")).join("");

  existing.innerHTML = `
    <div class="subsection-heading">
      <h3>${escapeHtml(t("hotTitle"))}</h3>
      <span>${escapeHtml(t("hotSubtitle"))}</span>
    </div>
    <div class="horizontal-strip">${hotCards || emptyState(t("hotEmpty"), true)}</div>
    <div class="subsection-heading subsection-heading--spaced">
      <h3>${escapeHtml(t("movesTitle"))}</h3>
      <span>${escapeHtml(state.moves.length ? t("movesSubtitle") : t("movesEmpty"))}</span>
    </div>
    <div class="compact-list">${movesCards || emptyState(t("movesEmpty"), true)}</div>
  `;
}

function renderSearchSuggestions() {
  const trending = document.getElementById("trending-searches");
  const recentBlock = document.getElementById("recent-searches-block");
  const recent = document.getElementById("recent-searches");

  trending.innerHTML = SEARCH_SUGGESTIONS.map(
    (item) => `<button type="button" class="chip" data-search-chip="${escapeHtml(item)}">${escapeHtml(item)}</button>`,
  ).join("");

  const searches = recentSearches();
  recentBlock.hidden = !searches.length;
  recent.innerHTML = searches
    .map((item) => `<button type="button" class="chip" data-search-chip="${escapeHtml(item)}">${escapeHtml(item)}</button>`)
    .join("");
}

function renderSaved() {
  const savedTarget = document.getElementById("saved-list");
  const recentTarget = document.getElementById("recently-opened-list");
  const saved = savedMarkets();
  const recent = recentlyOpened();

  savedTarget.innerHTML = saved.length
    ? saved.map((item) => savedCard(item, true)).join("")
    : `
      <div class="empty-state empty-state--compact">
        <strong>${escapeHtml(t("savedEmptyTitle"))}</strong>
        <span>${escapeHtml(t("savedEmptyCopy"))}</span>
      </div>
    `;

  recentTarget.innerHTML = recent.length
    ? recent.map((item) => savedCard(item, false)).join("")
    : emptyState(t("recentEmpty"), true);
}

function renderAllSavedButtons() {
  for (const button of document.querySelectorAll("[data-save-market]")) {
    try {
      const item = JSON.parse(decodeURIComponent(button.getAttribute("data-save-market")));
      button.textContent = isSaved(item.id) ? t("saved") : t("save");
    } catch {
      button.textContent = t("save");
    }
  }
}

async function refreshDashboard() {
  const [today, radar, hot, moves] = await Promise.all([
    loadJson("/api/today"),
    loadJson("/api/smart-money/active"),
    loadJson("/api/markets/hot"),
    loadJson("/api/markets/moves"),
  ]);

  renderToday(today);
  renderRadar(radar);
  renderHot(hot);
  renderMoves(moves);
  renderTodayExtras();
  renderSaved();
}

function updateContext() {
  const title = document.getElementById("context-title");
  const subtitle = document.getElementById("context-subtitle");
  const titleKeys = {
    today: "todayTab",
    radar: "radarTab",
    search: "searchTab",
    saved: "savedTab",
    more: "moreTab",
  };
  const subtitleKeys = {
    today: "todayContext",
    radar: "radarContext",
    search: "searchContext",
    saved: "savedContext",
    more: "moreContext",
  };
  title.textContent = t(titleKeys[state.activeTab]);
  subtitle.textContent = t(subtitleKeys[state.activeTab]);
}

function switchTab(tabName) {
  state.activeTab = tabName;
  for (const screen of document.querySelectorAll("[data-screen]")) {
    const active = screen.getAttribute("data-screen") === tabName;
    screen.classList.toggle("is-active", active);
    screen.hidden = !active;
  }
  for (const button of document.querySelectorAll("[data-tab]")) {
    button.classList.toggle("is-active", button.getAttribute("data-tab") === tabName);
  }
  updateContext();
  window.scrollTo({ top: 0, behavior: state.toggles.reducedAnimations ? "auto" : "smooth" });
}

function setupEvents() {
  document.addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;

    const tabButton = target.closest("[data-tab]");
    if (tabButton instanceof HTMLElement) {
      switchTab(tabButton.getAttribute("data-tab"));
      return;
    }

    if (target.matches("[data-refresh]")) {
      await refreshDashboard();
      return;
    }

    const searchChip = target.getAttribute("data-search-chip");
    if (searchChip) {
      document.getElementById("search-input").value = searchChip;
      await runSearch(searchChip);
      return;
    }

    const savePayload = target.getAttribute("data-save-market");
    if (savePayload) {
      saveMarket(JSON.parse(decodeURIComponent(savePayload)));
      return;
    }

    const removeId = target.getAttribute("data-remove-market");
    if (removeId) {
      removeSaved(removeId);
      return;
    }

    const openPayload = target.getAttribute("data-open-market");
    if (openPayload) {
      addRecentMarket(JSON.parse(decodeURIComponent(openPayload)));
      return;
    }

    const sharePayload = target.getAttribute("data-share-market");
    if (sharePayload) {
      await shareText(marketText(JSON.parse(decodeURIComponent(sharePayload))));
      target.textContent = t("copied");
      return;
    }

    const settingButton = target.closest("[data-setting]");
    if (settingButton instanceof HTMLElement) {
      const setting = settingButton.getAttribute("data-setting");
      const value = settingButton.getAttribute("data-value");
      if (setting === "language") {
        state.languageSetting = value;
        writeStorage("language", value);
      }
      if (setting === "theme") {
        state.themeSetting = value;
        writeStorage("theme", value);
      }
      applyTheme();
      applyCopy();
      rerenderCurrentData();
      return;
    }

    const toggleButton = target.closest("[data-toggle]");
    if (toggleButton instanceof HTMLElement) {
      const key = toggleButton.getAttribute("data-toggle");
      state.toggles[key] = !state.toggles[key];
      writeJsonStorage("toggles", state.toggles);
      applyTheme();
      updateSettingsControls();
      return;
    }

    const action = target.getAttribute("data-action");
    if (action === "share-today") {
      const text = state.today.slice(0, 3).map((item, index) => `${index + 1}. ${marketText(item)}`).join("\n\n");
      await shareText(text || t("todayEmpty"));
      target.textContent = t("copied");
      return;
    }
    if (action === "share-app") {
      await shareText(`${t("appShared")}\n${APP_URL}`);
      target.textContent = t("copied");
      return;
    }
    if (action === "feedback") {
      if (tg && tg.openTelegramLink) {
        tg.openTelegramLink(`${BOT_URL}?start=feedback`);
      } else {
        window.open(BOT_URL, "_blank", "noreferrer");
      }
    }
  });

  document.getElementById("search-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const query = document.getElementById("search-input").value.trim();
    await runSearch(query);
  });
}

async function runSearch(query) {
  if (!query) return;
  saveRecentSearch(query);
  const target = document.getElementById("search-results");
  target.innerHTML = emptyState(t("searchLoading"), true);
  const payload = await loadJson(`/api/search?q=${encodeURIComponent(query)}`);
  renderSearch(payload);
}

function rerenderCurrentData() {
  renderToday({ data: state.today });
  renderRadar({ data: state.radar });
  renderTodayExtras();
  renderSearch({ data: state.searchResults, message: t("searchNoResults") });
  renderSearchSuggestions();
  renderSaved();
}

applyTheme();
applyCopy();
renderSearchSuggestions();
setupEvents();
refreshDashboard();
