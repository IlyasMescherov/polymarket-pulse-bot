const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
const BOT_URL = "https://t.me/PulseMarketAIBot";
const APP_URL = "https://app.pulsemarketai.com/app";
const POLYMARKET_URL = "https://polymarket.com";
const EMPTY_MESSAGE = "No data yet. PulseMarket will keep watching.";
const STORAGE_PREFIX = "pulsemarket-miniapp:";
const SEARCH_SUGGESTIONS = ["bitcoin", "election", "fed", "ai", "sports"];
const EVENT_CATEGORIES = [
  { key: "all", en: "All", ru: "Все" },
  { key: "politics", en: "Politics", ru: "Политика" },
  { key: "crypto", en: "Crypto", ru: "Крипто" },
  { key: "ai", en: "AI", ru: "AI" },
  { key: "sports", en: "Sports", ru: "Спорт" },
  { key: "esports", en: "Esports", ru: "Киберспорт" },
  { key: "global", en: "Global", ru: "Мировые" },
  { key: "culture", en: "Culture", ru: "Культура" },
];

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
  selectedCategory: readStorage("selectedCategory", "all"),
  userInterests: readJsonStorage("userInterests", []),
  todayMeta: {},
  searchMeta: {},
  today: [],
  radar: [],
  hot: [],
  moves: [],
  searchResults: [],
  lastExplained: null,
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
    narrativeKicker: "Today’s Narrative",
    narrativeTitle: "What markets are reacting to today.",
    aiBriefingLabel: "AI briefing",
    interests: "Interests",
    interestsHint: "Prioritize categories you care about.",
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
    searchContextSummary: "Related market context",
    trendingSearches: "Trending searches",
    recentSearches: "Recent searches",
    returnLater: "Return later",
    savedTitle: "Saved markets",
    savedSubtitle: "Your personal feed to return to later.",
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
    aboutPulse: "About PulseMarket AI",
    aboutPulseCopy: "A calm daily intelligence companion for Polymarket.",
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
    pulseWorthWatching: "Worth watching",
    pulseHighAttention: "High attention",
    pulseQuiet: "Quiet",
    pulseHeating: "Heating up",
    pulseTrending: "Trending",
    whyItMatters: "Why people care",
    whyPeopleCare: "Why people care",
    watchNext: "Watch",
    watchNextCopy: "Probability, activity, and resolution rules.",
    marketMood: "Market Mood",
    exploreMarket: "Explore Market",
    open: "Open",
    explain: "Explain",
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
    savedEmptyCopy: "Save markets to build your daily feed.",
    recentEmpty: "No opened markets yet.",
    searchLoading: "Searching markets...",
    searchNoResults: "No markets found.",
    veryLow: "Unlikely",
    lowButActive: "Low probability, but this market may still be active.",
    marketAttentionRising: "People are paying more attention to this market.",
    worthWatching: "Worth watching today.",
    activeToday: "Attention grew around this market.",
    attentionMoved: "Public attention is rising.",
    quietNote: "No major shift yet.",
    endingSoonOne: "market is ending soon.",
    endingSoonMany: "markets are ending soon.",
    movesOne: "market changed enough to review.",
    movesMany: "markets changed enough to review.",
    whatChangedTitle: "What changed",
    moodTodayTitle: "Market mood today",
    moodSummaryEmpty: "Markets are quiet right now.",
    categoryGeopolitics: "Geopolitics",
    categoryCrypto: "Crypto",
    categorySports: "Sports",
    categoryOther: "Market activity",
    moodLineActive: "active",
    moodLineHeating: "heating up",
    moodLineQuiet: "quiet",
    selectedToday: "Selected for today’s market scan.",
    categoryAll: "All",
    simpleReadTitle: "Simple Read",
    simpleReadCopy: "This market asks whether an event will happen. Watch the probability and rules before drawing conclusions.",
    whatMarketAsks: "What this market asks",
    whatChangedDetail: "What changed",
    whatThisMeans: "What this means",
    attentionVsConviction: "Attention vs conviction",
    howSerious: "How serious is this movement",
    whatInfluences: "What can influence it",
    influencingFactorsCopy: "News context, public activity, time left, and resolution rules.",
    relatedTopics: "Related topics",
    resolutionRules: "Resolution rules",
    resolutionRulesCopy: "Open the market page and review the official resolution criteria.",
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
    narrativeKicker: "Нарратив дня",
    narrativeTitle: "На что сегодня реагируют рынки.",
    aiBriefingLabel: "AI обзор",
    interests: "Интересы",
    interestsHint: "Выбери категории, которые важнее для тебя.",
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
    searchContextSummary: "Контекст по запросу",
    trendingSearches: "Популярные запросы",
    recentSearches: "Недавние запросы",
    returnLater: "Вернуться позже",
    savedTitle: "Сохранённые рынки",
    savedSubtitle: "Твой личный feed, к которому можно вернуться.",
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
    aboutPulse: "О PulseMarket AI",
    aboutPulseCopy: "Спокойный ежедневный помощник по Polymarket.",
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
    pulseWorthWatching: "Стоит изучить",
    pulseHighAttention: "Высокое внимание",
    pulseQuiet: "Тихо",
    pulseHeating: "Разогревается",
    pulseTrending: "В тренде",
    whyItMatters: "Почему это важно",
    whyPeopleCare: "Почему людям это интересно",
    watchNext: "За чем следить",
    watchNextCopy: "Вероятность, активность и правила разрешения.",
    marketMood: "Настроение рынка",
    exploreMarket: "Открыть рынок",
    open: "Открыть",
    explain: "Подробнее",
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
    savedEmptyCopy: "Сохраняй рынки, чтобы собрать личный daily feed.",
    recentEmpty: "Открытых рынков пока нет.",
    searchLoading: "Ищу рынки...",
    searchNoResults: "Рынки не найдены.",
    veryLow: "Маловероятно",
    lowButActive: "Вероятность низкая, но рынок может быть активным.",
    marketAttentionRising: "К этому рынку растёт внимание.",
    worthWatching: "Сегодня стоит изучить.",
    activeToday: "Интерес к этому рынку вырос.",
    attentionMoved: "Публичное внимание растёт.",
    quietNote: "Без больших изменений.",
    endingSoonOne: "рынок скоро завершится.",
    endingSoonMany: "рынка скоро завершатся.",
    movesOne: "рынок заметно изменился.",
    movesMany: "рынка заметно изменились.",
    whatChangedTitle: "Что изменилось",
    moodTodayTitle: "Настроение дня",
    moodSummaryEmpty: "Рынки сейчас спокойны.",
    categoryGeopolitics: "Геополитика",
    categoryCrypto: "Крипта",
    categorySports: "Спорт",
    categoryOther: "Активность рынка",
    moodLineActive: "активна",
    moodLineHeating: "разогревается",
    moodLineQuiet: "спокойна",
    selectedToday: "Отобран для короткого обзора.",
    categoryAll: "Все",
    simpleReadTitle: "Простой смысл",
    simpleReadCopy: "Этот рынок спрашивает, произойдёт ли событие. Смотри на вероятность и правила разрешения, прежде чем делать выводы.",
    whatMarketAsks: "О чём рынок",
    whatChangedDetail: "Что изменилось",
    whatThisMeans: "Что это значит",
    attentionVsConviction: "Внимание vs убеждённость",
    howSerious: "Насколько движение серьёзное",
    whatInfluences: "Что влияет на рынок",
    influencingFactorsCopy: "Новости, публичная активность, время до завершения и правила разрешения.",
    relatedTopics: "Связанные темы",
    resolutionRules: "Правила разрешения",
    resolutionRulesCopy: "Открой страницу рынка и проверь официальные критерии разрешения.",
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

function categoryLabel(key) {
  if (key === "other") return t("categoryOther");
  const category = EVENT_CATEGORIES.find((item) => item.key === key) || EVENT_CATEGORIES[0];
  return isRu() ? category.ru : category.en;
}

function categoryForItem(item) {
  if (item && item.category) return String(item.category);
  const title = String((item && item.title) || "").toLowerCase();
  if (/(trump|election|president|senate|iran|israel|china|russia|ukraine|war|diplomacy)/.test(title)) return "politics";
  if (/(bitcoin|btc|ethereum|eth|solana|xrp|crypto|binance|coinbase)/.test(title)) return "crypto";
  if (/(openai|nvidia|tesla|apple|google|microsoft|anthropic|robot| ai )/.test(` ${title} `)) return "ai";
  if (/(nba|nfl|ufc|soccer|football|tennis|baseball|fifa|playoff)/.test(title)) return "sports";
  if (/(cs2|dota|valorant|league of legends|esports)/.test(title)) return "esports";
  if (/(oscars|grammy|movie|film|music|celebrity|youtube|twitter)/.test(title)) return "culture";
  return "global";
}

function selectedCategory() {
  return EVENT_CATEGORIES.some((item) => item.key === state.selectedCategory)
    ? state.selectedCategory
    : "all";
}

function filterBySelectedCategory(items) {
  const selected = selectedCategory();
  const base = Array.isArray(items) ? items : [];
  if (selected === "all") return prioritizeInterests(base);
  return base.filter((item) => categoryForItem(item) === selected);
}

function prioritizeInterests(items) {
  if (!state.userInterests.length) return items;
  return [...items].sort((left, right) => {
    const leftScore = state.userInterests.includes(categoryForItem(left)) ? 1 : 0;
    const rightScore = state.userInterests.includes(categoryForItem(right)) ? 1 : 0;
    return rightScore - leftScore;
  });
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
  renderCategoryChips();
  renderInterestChips();
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

function probabilityDisplay(item) {
  const label = probabilityMeaning(item);
  const number = probability(item);
  if (label === number) return label;
  return `${label} · ${number}`;
}

function probabilityMeaning(item) {
  const value = item && item.probability !== null && item.probability !== undefined ? Number(item.probability) : null;
  if (value === null || Number.isNaN(value)) return isRu() ? "Пока нет данных" : "Unknown";
  if (value < 15) return isRu() ? "Маловероятно" : "Unlikely";
  if (value < 45) return isRu() ? "Возможно" : "Possible";
  if (value < 75) return isRu() ? "Вероятно" : "Likely";
  return isRu() ? "Очень вероятно" : "Highly likely";
}

function isGenericReason(value) {
  const text = String(value || "").trim().toLowerCase();
  if (!text) return true;
  return [
    "this market is active today",
    "people are watching because activity " + "increased",
    "people are paying attention, but the story is still early",
    "activity " + "increased",
    "public activity is above the visibility threshold",
    "public attention is rising around this market",
    "этот рынок выделяется в сегодняшнем обзоре",
    "активность выросла",
    "публичное внимание растёт",
  ].some((fragment) => text.includes(fragment));
}

function matchesCurrentLanguage(value) {
  const text = String(value || "");
  if (!text.trim()) return false;
  const hasCyrillic = /[а-яё]/i.test(text);
  return isRu() ? hasCyrillic : !hasCyrillic;
}

function localizedText(value, fallback) {
  return matchesCurrentLanguage(value) ? String(value).trim() : fallback;
}

function editorialReason(item) {
  const mood = marketMood(item || {});
  if (mood.key === "ending_soon") {
    return isRu() ? "Рынок близок к разрешению, поэтому внимание выше." : "The market is close to resolution, so attention is higher.";
  }
  if (mood.key === "volatile") {
    return isRu() ? "Вероятность заметно изменилась, и рынок стал заметнее." : "Probability moved enough to make this market stand out.";
  }

  const title = String((item && item.title) || "").toLowerCase();
  const category = categoryForItem(item || {});
  if (/(bitcoin|btc|ethereum|eth|crypto|binance|coinbase)/.test(title) || category === "crypto") {
    return isRu() ? "Активность усилилась после движения крипторынка." : "Crypto volatility brought more attention to this market.";
  }
  if (/(iran|israel|trump|election|president|senate|war|diplomacy|china|russia|ukraine)/.test(title) || category === "politics" || category === "global") {
    return isRu() ? "Внимание выросло вокруг политической повестки." : "Attention increased around political headlines.";
  }
  if (/(nba|nfl|ufc|soccer|football|tennis|baseball|fifa|playoff|match)/.test(title) || category === "sports") {
    return isRu() ? "Рынок оживился перед спортивным событием." : "Activity grew ahead of the event.";
  }
  if (/(openai|nvidia|anthropic|robot| ai )/.test(` ${title} `) || category === "ai") {
    return isRu() ? "Внимание к AI-теме усилилось." : "AI-related attention increased today.";
  }
  if (Number((item && item.public_activity) || 0) > 0) {
    return isRu() ? "Публичное внимание к этому рынку растёт." : "Public attention is rising around this market.";
  }
  return isRu() ? "Пользователи активнее следят за развитием темы." : "Users started watching this topic more actively.";
}

function pulseLabel(item) {
  const score = Number((item && item.pulse_score) || 0);
  if (score >= 85) return t("pulseTrending");
  if (score >= 70) return t("pulseHighAttention");
  if (score >= 50) return t("pulseWorthWatching");
  if (score >= 35) return t("pulseHeating");
  return t("pulseQuiet");
}

function pulseMeta(item) {
  return `Pulse ${escapeHtml((item && item.pulse_score) ?? 0)}/100`;
}

function pulseSecondary(item) {
  return `<span class="pulse-subtle">${escapeHtml(pulseLabel(item))} · ${pulseMeta(item)}</span>`;
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

function compactTitle(title, limit = 72) {
  const value = String(title || "Untitled market").trim();
  return value.length > limit ? `${value.slice(0, limit - 1).trim()}…` : value;
}

function shortReason(item) {
  if (item && item.what_this_means && matchesCurrentLanguage(item.what_this_means) && !isGenericReason(item.what_this_means)) {
    const sentence = String(item.what_this_means).split(".")[0].trim();
    return sentence ? `${sentence}.` : t("selectedToday");
  }
  if (item && item.why_people_care && matchesCurrentLanguage(item.why_people_care) && !isGenericReason(item.why_people_care)) {
    const sentence = String(item.why_people_care).split(".")[0].trim();
    return sentence ? `${sentence}.` : t("selectedToday");
  }
  if (item && item.why_it_matters && matchesCurrentLanguage(item.why_it_matters) && !isGenericReason(item.why_it_matters)) {
    const sentence = String(item.why_it_matters).split(".")[0].trim();
    return sentence ? `${sentence}.` : t("selectedToday");
  }
  if (item && Number(item.probability) > 0 && Number(item.probability) < 1) return t("lowButActive");
  return editorialReason(item || {});
}

function attentionSignal(item) {
  const raw = String((item && item.attention_signal) || "");
  const movement = Math.abs(Number((item && item.movement) || 0));
  const activity = Number((item && (item.public_activity || item.volume)) || 0);
  let key = "moderate";
  if (/meaningful|значимое/i.test(raw)) key = "meaningful";
  else if (/strong|сильн/i.test(raw)) key = "strong";
  else if (/noise|шум/i.test(raw)) key = "noise";
  else if (movement >= 5 && activity >= 100000) key = "meaningful";
  else if (movement >= 3 || activity >= 500000) key = "strong";
  else if (movement < 1 && activity < 100000) key = "noise";
  const en = {
    noise: "Noise",
    moderate: "Moderate attention",
    strong: "Strong interest",
    meaningful: "Meaningful attention shift",
  };
  const ru = {
    noise: "Шум",
    moderate: "Умеренное внимание",
    strong: "Сильный интерес",
    meaningful: "Значимое движение внимания",
  };
  return (isRu() ? ru : en)[key];
}

function topicLabel(value) {
  const text = String(value || "").trim();
  if (!isRu()) return text;
  const labels = {
    "Bitcoin": "Bitcoin",
    "Crypto volatility": "Волатильность крипты",
    "US politics": "Политика США",
    "Geopolitics": "Геополитика",
    "AI": "AI",
    "Sports": "Спорт",
    "Esports": "Киберспорт",
    "Culture": "Культура",
    "Global": "Мировые события",
  };
  return labels[text] || text;
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
      active: "Публичное внимание уже есть.",
      heating_up: "Внимание к этому рынку растёт.",
      volatile: "Вероятность заметно изменилась, поэтому рынок выделяется.",
      ending_soon: "Рынок близок к разрешению.",
    }[key] || "Сильного движения пока нет.";
  }
  return {
    quiet: "No strong movement yet.",
    active: "Public attention is present.",
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
    probability_interpretation: item && item.probability_interpretation,
    pulse_score: item && item.pulse_score,
    why: shortReason(item || {}),
    simple_read: item && item.simple_read,
    what_to_watch: item && item.what_to_watch,
    attention_summary: item && item.attention_summary,
    topic_narrative: item && item.topic_narrative,
    what_this_means: item && item.what_this_means,
    attention_signal: item && item.attention_signal,
    attention_vs_conviction: item && item.attention_vs_conviction,
    related_topics: Array.isArray(item && item.related_topics) ? item.related_topics : [],
    category: categoryForItem(item || {}),
    category_label: item && item.category_label,
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
  return `${item.title || "Polymarket market"}\n${t("probability")}: ${probability(item)}\n${t("marketMood")}: ${mood.label}\n${pulseLabel(item)} · ${item.pulse_score ?? 0}/100\n${t("whyPeopleCare")}: ${shortReason(item)}\n${safeUrl(item.url)}`;
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

function detailActionRow(item) {
  const encoded = encodeURIComponent(JSON.stringify(normalizeMarket(item)));
  return `<div class="action-row">${detailActionButtons(item, encoded)}</div>`;
}

function detailActionButtons(item, encoded = encodeURIComponent(JSON.stringify(normalizeMarket(item)))) {
  const saved = isSaved(item);
  return `
    <a class="primary-action" href="${escapeHtml(safeUrl(item && item.url))}" target="_blank" rel="noreferrer" data-open-market="${encoded}">${escapeHtml(t("open"))}</a>
    <button type="button" class="soft-action" data-save-market="${encoded}">${escapeHtml(saved ? t("saved") : t("save"))}</button>
    <button type="button" class="soft-action" data-share-market="${encoded}">${escapeHtml(t("share"))}</button>
  `;
}

function buttonRow(item) {
  const encoded = encodeURIComponent(JSON.stringify(normalizeMarket(item)));
  return `
    <div class="action-row action-row--compact">
      <a class="primary-action" href="${escapeHtml(safeUrl(item && item.url))}" target="_blank" rel="noreferrer" data-open-market="${encoded}">${escapeHtml(t("open"))}</a>
      <button type="button" class="soft-action" data-explain-market="${encoded}">${escapeHtml(t("explain"))}</button>
    </div>
  `;
}

function marketCard(item, variant = "compact") {
  const mood = marketMood(item);
  return `
    <article class="market-card market-card--${variant}">
      <div class="market-card__main">
        <div class="market-card__titleline">
          <h3>${escapeHtml(compactTitle(item.title))}</h3>
          <span class="pill pill--mood">${escapeHtml(mood.label)}</span>
        </div>
        <p>${escapeHtml(shortReason(item))}</p>
      </div>
      <div class="pill-row">
        <span class="pill pill--prob">${escapeHtml(probabilityDisplay(item))}</span>
      </div>
      ${pulseSecondary(item)}
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
        <div class="market-card__titleline">
          <h3>${escapeHtml(compactTitle(item.title))}</h3>
          <span class="pill pill--mood">${escapeHtml(mood.label)}</span>
        </div>
        <p>${escapeHtml(item.why || t("selectedToday"))}</p>
      </div>
      <div class="pill-row">
        <span class="pill pill--prob">${escapeHtml(probabilityDisplay(item))}</span>
      </div>
      ${pulseSecondary(item)}
      <div class="action-row">
        <a class="primary-action" href="${escapeHtml(safeUrl(item.url))}" target="_blank" rel="noreferrer" data-open-market="${encoded}">${escapeHtml(t("open"))}</a>
        ${
          removable
            ? `<button type="button" class="soft-action" data-remove-market="${escapeHtml(item.id)}">${escapeHtml(t("remove"))}</button>`
            : `<button type="button" class="soft-action" data-explain-market="${encoded}">${escapeHtml(t("explain"))}</button>`
        }
      </div>
    </article>
  `;
}

function openExplain(item) {
  const normalized = normalizeMarket(item);
  state.lastExplained = normalized;
  const sheet = document.getElementById("explain-sheet");
  const title = document.getElementById("explain-title");
  const body = document.getElementById("explain-body");
  const actions = document.getElementById("explain-actions");
  const mood = marketMood(normalized);
  const topics = Array.isArray(normalized.related_topics) && normalized.related_topics.length
    ? normalized.related_topics.map(topicLabel).join(", ")
    : categoryLabel(normalized.category || "global");

  title.textContent = normalized.title;
  body.innerHTML = `
    <div class="detail-list">
      <div>
        <span>${escapeHtml(t("whatMarketAsks"))}</span>
        <strong>${escapeHtml(localizedText(normalized.simple_read, t("simpleReadCopy")))}</strong>
      </div>
      <div>
        <span>${escapeHtml(t("whyPeopleCare"))}</span>
        <strong>${escapeHtml(normalized.why || shortReason(normalized))}</strong>
      </div>
      <div>
        <span>${escapeHtml(t("whatChangedDetail"))}</span>
        <strong>${escapeHtml(localizedText(normalized.attention_summary, mood.reason || editorialReason(normalized)))}</strong>
      </div>
      <div>
        <span>${escapeHtml(t("whatThisMeans"))}</span>
        <strong>${escapeHtml(localizedText(normalized.what_this_means, editorialReason(normalized)))}</strong>
      </div>
      <div>
        <span>${escapeHtml(t("attentionVsConviction"))}</span>
        <strong>${escapeHtml(localizedText(normalized.attention_vs_conviction, mood.reason || editorialReason(normalized)))}</strong>
      </div>
      <div>
        <span>${escapeHtml(t("howSerious"))}</span>
        <strong>${escapeHtml(attentionSignal(normalized))}</strong>
      </div>
      <div>
        <span>${escapeHtml(t("whatInfluences"))}</span>
        <strong>${escapeHtml(localizedText(normalized.what_to_watch, t("influencingFactorsCopy")))}</strong>
      </div>
      <div>
        <span>${escapeHtml(t("marketMood"))}</span>
        <strong>${escapeHtml(mood.label)} · ${escapeHtml(mood.reason)}</strong>
      </div>
      <div>
        <span>${escapeHtml(t("relatedTopics"))}</span>
        <strong>${escapeHtml(topics)}</strong>
      </div>
      <div>
        <span>${escapeHtml(t("resolutionRules"))}</span>
        <strong>${escapeHtml(t("resolutionRulesCopy"))}</strong>
      </div>
    </div>
  `;
  actions.innerHTML = detailActionButtons(normalized);
  sheet.hidden = false;
  document.documentElement.classList.add("sheet-open");
}

function closeExplain() {
  const sheet = document.getElementById("explain-sheet");
  sheet.hidden = true;
  document.documentElement.classList.remove("sheet-open");
}

function moodWeight(key) {
  return {
    ending_soon: 4,
    volatile: 4,
    heating_up: 3,
    active: 2,
    quiet: 1,
  }[key] || 1;
}

function moodSummaryWord(key) {
  if (key === "heating_up" || key === "volatile" || key === "ending_soon") return t("moodLineHeating");
  if (key === "active") return t("moodLineActive");
  return t("moodLineQuiet");
}

function editorialChange(category, moodKey = "active") {
  const heating = moodKey === "heating_up" || moodKey === "volatile" || moodKey === "ending_soon";
  const en = {
    politics: heating ? "🔥 Political markets became more active" : "👀 Political attention increased",
    crypto: heating ? "📈 Crypto activity returned" : "👀 Crypto attention increased",
    ai: "👀 AI attention increased",
    sports: heating ? "🔥 Sports markets heated up" : "👀 Sports markets drew more attention",
    esports: heating ? "🔥 Esports markets heated up" : "👀 Esports markets drew more attention",
    culture: "👀 Culture markets drew attention",
    global: "🔥 Global events became more active",
    other: "👀 Market attention increased",
  };
  const ru = {
    politics: heating ? "🔥 Политические рынки оживились" : "👀 Внимание к политике усилилось",
    crypto: heating ? "📈 Крипта снова активна" : "👀 Внимание к крипте усилилось",
    ai: "👀 Внимание к AI усилилось",
    sports: heating ? "🔥 Спорт разогревается" : "👀 Активность в спорте выросла",
    esports: heating ? "🔥 Киберспорт разогревается" : "👀 Активность в киберспорте выросла",
    culture: "👀 Культурные рынки заметнее",
    global: "🔥 Мировые события активнее",
    other: "👀 Внимание к рынкам выросло",
  };
  return (isRu() ? ru : en)[category] || (isRu() ? ru.other : en.other);
}

function editorialHeadline(category) {
  const en = {
    politics: "Politics is the main market story today.",
    crypto: "Crypto is the main market story today.",
    ai: "AI attention is shaping today’s market read.",
    sports: "Sports markets are heating up today.",
    esports: "Esports markets are active today.",
    culture: "Culture markets are drawing attention today.",
    global: "Global events are shaping today’s market read.",
    other: "PulseMarket is reading today’s market attention.",
  };
  const ru = {
    politics: "Политика — главная история рынка сегодня.",
    crypto: "Крипта — главная история рынка сегодня.",
    ai: "AI формирует сегодняшнюю картину рынка.",
    sports: "Спортивные рынки сегодня разогреваются.",
    esports: "Киберспорт сегодня активен.",
    culture: "Культурные рынки сегодня заметнее.",
    global: "Мировые события формируют картину дня.",
    other: "PulseMarket читает сегодняшнее внимание рынка.",
  };
  return (isRu() ? ru : en)[category] || (isRu() ? ru.other : en.other);
}

function rankedMoodCategories(markets) {
  const summary = new Map();
  for (const item of markets) {
    const category = categoryForItem(item);
    const mood = marketMood(item);
    const current = summary.get(category);
    if (!current || moodWeight(mood.key) > moodWeight(current.key)) {
      summary.set(category, mood);
    }
  }
  return Array.from(summary.entries())
    .sort((left, right) => moodWeight(right[1].key) - moodWeight(left[1].key))
    .filter(([category]) => category !== "other");
}

function renderDailySnapshot() {
  const changed = document.getElementById("what-changed");
  const moodTarget = document.getElementById("mood-summary");
  if (!changed || !moodTarget) return;

  clearNode(changed);
  clearNode(moodTarget);

  const allMarkets = [...state.today, ...state.hot, ...state.moves];
  const notes = [];
  if (Array.isArray(state.todayMeta.what_changed)) {
    notes.push(...state.todayMeta.what_changed.filter((item) => matchesCurrentLanguage(item)));
  }
  const moodCategories = rankedMoodCategories(allMarkets);
  notes.push(...moodCategories.slice(0, 2).map(([category, mood]) => editorialChange(category, mood.key)));
  if (state.radar[0]) {
    notes.push(editorialChange(categoryForItem(state.radar[0]), "heating_up"));
  }
  const endingSoon = allMarkets.filter((item) => marketMood(item).key === "ending_soon").length;
  if (endingSoon) notes.push(`⚠️ ${endingSoon} ${t(endingSoon === 1 ? "endingSoonOne" : "endingSoonMany")}`);
  if (state.moves.length) notes.push(`⚡ ${state.moves.length} ${t(state.moves.length === 1 ? "movesOne" : "movesMany")}`);
  const uniqueNotes = [...new Set(notes)];
  if (!uniqueNotes.length) uniqueNotes.push(`• ${t("quietNote")}`);

  changed.innerHTML = `
    <div class="mini-panel__header">
      <h3>${escapeHtml(t("whatChangedTitle"))}</h3>
    </div>
    <div class="change-list">
      ${uniqueNotes.slice(0, 3).map((note) => `<p>${escapeHtml(note)}</p>`).join("")}
    </div>
  `;

  const rows = moodCategories.slice(0, 3);
  const fallbackRows = rows.length ? rows : [["other", { key: "quiet" }]];

  moodTarget.innerHTML = `
    <div class="mini-panel__header">
      <h3>${escapeHtml(t("moodTodayTitle"))}</h3>
    </div>
    <div class="mood-row">
      ${fallbackRows
        .map(
          ([category, mood]) =>
            `<span>${escapeHtml(categoryLabel(category))} <strong>${escapeHtml(moodSummaryWord(mood.key))}</strong></span>`,
        )
        .join("")}
    </div>
  `;
}

function renderNarrative() {
  const target = document.getElementById("today-narrative");
  if (!target) return;
  clearNode(target);

  const category = selectedCategory();
  const moodCategories = rankedMoodCategories([...state.today, ...state.hot, ...state.moves]);
  const topCategory = category !== "all" ? category : (moodCategories[0] && moodCategories[0][0]) || "other";
  const apiHeadline = localizedText(state.todayMeta.narrative, "");
  const apiInterpretation = localizedText(state.todayMeta.interpretation, "");
  const headline = apiHeadline || editorialHeadline(topCategory);
  const changes = moodCategories
    .slice(0, 3)
    .map(([itemCategory, mood]) => editorialChange(itemCategory, mood.key));

  target.innerHTML = `
    <p class="section-kicker">${escapeHtml(t("aiBriefingLabel"))}</p>
    <h3>${escapeHtml(headline)}</h3>
    ${apiInterpretation ? `<p>${escapeHtml(apiInterpretation)}</p>` : ""}
    ${
      changes.length
        ? `<div class="narrative-points">${changes.map((item) => `<span>${escapeHtml(item)}</span>`).join("")}</div>`
        : ""
    }
  `;
}

function renderToday(payload) {
  state.today = dataFrom(payload);
  state.todayMeta = {
    narrative: payload && payload.narrative,
    interpretation: payload && payload.interpretation,
    what_changed: Array.isArray(payload && payload.what_changed) ? payload.what_changed : [],
    category_summaries: (payload && payload.category_summaries) || {},
  };
  const hero = document.getElementById("today-hero");
  const secondary = document.getElementById("today-secondary");
  clearNode(hero);
  secondary.innerHTML = "";

  const visibleToday = filterBySelectedCategory(state.today);
  renderNarrative();
  if (!visibleToday.length) {
    hero.innerHTML = emptyState(t("todayEmpty"));
    return;
  }

  const top = visibleToday[0];
  const topMood = marketMood(top);
  hero.innerHTML = `
    <div class="story-card__topline">
      <span>${escapeHtml(t("mainStory"))}</span>
      <span>${escapeHtml(pulseLabel(top))}</span>
    </div>
    <h3>${escapeHtml(compactTitle(top.title, 86))}</h3>
    <div class="pill-row">
      <span class="pill pill--prob">${escapeHtml(probabilityDisplay(top))}</span>
      <span class="pill pill--mood">${escapeHtml(topMood.label)}</span>
    </div>
    ${pulseSecondary(top)}
    <p>${escapeHtml(shortReason(top))}</p>
    ${buttonRow(top)}
  `;

  secondary.innerHTML = visibleToday.slice(1, 4).map((item) => marketCard(item, "secondary")).join("");
}

function renderRadar(payload) {
  state.radar = dataFrom(payload);
  const hero = document.getElementById("smart-hero");
  const list = document.getElementById("radar-list");
  clearNode(hero);
  list.innerHTML = "";

  const visibleRadar = filterBySelectedCategory(state.radar);
  if (!visibleRadar.length) {
    hero.innerHTML = emptyState(t("radarEmpty"), true);
    return;
  }

  const top = visibleRadar[0];
  hero.innerHTML = `
    <div class="story-card__topline">
      <span>${escapeHtml(t("radarTitle"))}</span>
      <span>${escapeHtml(compactUsd(top.public_activity))}</span>
    </div>
    <h3>${escapeHtml(compactTitle(top.title || "Public market activity", 82))}</h3>
    <p>${escapeHtml(shortReason(top))}</p>
    ${buttonRow({ ...top, pulse_score: top.pulse_score || 0, probability: top.probability })}
  `;

  const rest = visibleRadar.slice(1, 5);
  if (rest.length) {
    list.innerHTML = `
      <h3 class="list-title">${escapeHtml(t("radarListTitle"))}</h3>
      ${rest
        .map(
          (item) => `
            <article class="activity-row">
              <div>
                <h4>${escapeHtml(item.title || "Public market activity")}</h4>
                <p>${escapeHtml(shortReason(item))}</p>
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
  state.searchMeta = { summary: payload && payload.summary };
  const target = document.getElementById("search-results");
  const localizedSummary = localizedText(
    state.searchMeta.summary,
    state.searchResults[0] ? editorialReason(state.searchResults[0]) : "",
  );
  const summary = localizedSummary
    ? `<div class="search-summary"><span>${escapeHtml(t("searchContextSummary"))}</span><strong>${escapeHtml(localizedSummary)}</strong></div>`
    : "";
  target.innerHTML = state.searchResults.length
    ? summary + state.searchResults.slice(0, 5).map((item) => marketCard(item, "search")).join("")
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

  const hotCards = filterBySelectedCategory(state.hot).slice(0, 5).map((item) => marketCard(item, "compact")).join("");
  const movesCards = filterBySelectedCategory(state.moves).slice(0, 3).map((item) => marketCard(item, "compact")).join("");

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

  const categorySuggestions = selectedCategory() === "all"
    ? SEARCH_SUGGESTIONS
    : [categoryLabel(selectedCategory()).toLowerCase(), ...SEARCH_SUGGESTIONS].slice(0, 5);
  trending.innerHTML = categorySuggestions.map(
    (item) => `<button type="button" class="chip" data-search-chip="${escapeHtml(item)}">${escapeHtml(item)}</button>`,
  ).join("");

  const searches = recentSearches();
  recentBlock.hidden = !searches.length;
  recent.innerHTML = searches
    .map((item) => `<button type="button" class="chip" data-search-chip="${escapeHtml(item)}">${escapeHtml(item)}</button>`)
    .join("");
}

function renderCategoryChips() {
  const target = document.getElementById("category-chips");
  if (!target) return;
  target.innerHTML = EVENT_CATEGORIES.map((category) => {
    const active = selectedCategory() === category.key;
    return `<button type="button" class="category-chip${active ? " is-active" : ""}" data-category="${category.key}">${escapeHtml(categoryLabel(category.key))}</button>`;
  }).join("");
}

function renderInterestChips() {
  const target = document.getElementById("interest-chips");
  if (!target) return;
  target.innerHTML = EVENT_CATEGORIES.filter((category) => category.key !== "all").map((category) => {
    const active = state.userInterests.includes(category.key);
    return `<button type="button" class="chip chip--interest${active ? " is-active" : ""}" data-interest="${category.key}">${escapeHtml(categoryLabel(category.key))}</button>`;
  }).join("");
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
  renderDailySnapshot();
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

    const category = target.getAttribute("data-category");
    if (category) {
      state.selectedCategory = category;
      writeStorage("selectedCategory", category);
      renderCategoryChips();
      renderSearchSuggestions();
      rerenderCurrentData();
      return;
    }

    const interest = target.getAttribute("data-interest");
    if (interest) {
      state.userInterests = state.userInterests.includes(interest)
        ? state.userInterests.filter((item) => item !== interest)
        : [...state.userInterests, interest];
      writeJsonStorage("userInterests", state.userInterests);
      renderInterestChips();
      rerenderCurrentData();
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

    const explainPayload = target.getAttribute("data-explain-market");
    if (explainPayload) {
      openExplain(JSON.parse(decodeURIComponent(explainPayload)));
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
    if (action === "close-explain") {
      closeExplain();
      return;
    }
  });

  document.getElementById("explain-sheet").addEventListener("click", (event) => {
    if (event.target === event.currentTarget) closeExplain();
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
  renderDailySnapshot();
  renderSearch({ data: state.searchResults, message: t("searchNoResults") });
  renderSearchSuggestions();
  renderSaved();
}

applyTheme();
applyCopy();
renderCategoryChips();
renderInterestChips();
renderSearchSuggestions();
setupEvents();
refreshDashboard();
