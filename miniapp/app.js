const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
const BOT_URL = "https://t.me/PulseMarketAIBot";
const APP_URL = "https://app.pulsemarketai.com/app";
const POLYMARKET_URL = "https://polymarket.com";
const EMPTY_MESSAGE = "No data yet. PulseMarket will keep watching.";
const BOOT_LOADING_MIN_MS = 520;
const STORAGE_PREFIX = "pulsemarket-miniapp:";
const SEARCH_SUGGESTIONS = ["bitcoin", "election", "fed", "ai", "sports"];
const TELEGRAM_CHROME_COLORS = {
  dark: { header: "#050910", background: "#050910" },
  light: { header: "#f4f7fb", background: "#f4f7fb" },
};
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
  themeSetting: readStorage("theme", "dark"),
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
  loading: {
    today: true,
    radar: true,
    hot: true,
    moves: true,
  },
  errors: {},
};

const copy = {
  en: {
    productLine: "Understand what matters on Polymarket.",
    researchLabel: "Research only · No trade execution",
    botLink: "Bot",
    refresh: "Refresh",
    loadingTitle: "Preparing market briefing",
    loadingStepMarkets: "collecting markets",
    loadingStepActivity: "comparing activity",
    loadingStepChanges: "checking changes",
    loadingStepAnalysis: "preparing short analysis",
    apiErrorTitle: "Could not load briefing.",
    apiErrorCopy: "Try refreshing in a few seconds.",
    errorRefresh: "Refresh",
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
    eventDesk: "Event intelligence desk",
    topStory: "Top story",
    storyContext: "Story context",
    storyFrontPage: "Today’s market stories",
    openStory: "Open story",
    linkedMarkets: "Linked markets",
    storyConfidence: "Confidence",
    storySources: "Sources",
    storyChanged: "What changed in this story",
    storyFallback: "No strong connected story yet. PulseMarket is watching related markets.",
    pulseKicker: "Daily pulse",
    marketToday: "Market today",
    updatedAt: "Updated",
    updatedJustNow: "Updated just now",
    staleBriefing: "Showing last briefing, refreshing in background",
    narrativeKicker: "Today’s Narrative",
    narrativeTitle: "What markets are reacting to today.",
    aiBriefingLabel: "AI briefing",
    newsContext: "News context",
    newsHigh: "News: high",
    newsMedium: "News: medium",
    newsLow: "News: low",
    officialSource: "Official source",
    socialBuzz: "Social buzz",
    noStrongNews: "No strong news",
    whyMovingNow: "Why moving now",
    latestImportantNews: "Latest important news",
    sourcesLabel: "Sources",
    officialConfirmation: "Official confirmation",
    whatToVerify: "What to verify",
    todayReactsTo: "Today markets react to",
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
    moreSubtitle: "Tune the app and learn how the market read works.",
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
    pulseWorthWatching: "Notable",
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
    explain: "Analysis",
    save: "Save",
    saved: "Saved",
    remove: "Remove",
    share: "Share",
    publicActivity: "Public activity",
    activityLevel: "Activity level",
    radarEmpty: "No strong public activity detected right now. PulseMarket will keep watching.",
    radarReason: "This market stands out in the attention layer.",
    radarListTitle: "More markets getting attention",
    todayEmpty: "PulseMarket is preparing today’s intelligence.",
    hotTitle: "Hot markets",
    hotSubtitle: "Markets with strong current activity.",
    viewAll: "View all",
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
    marketAttentionRising: "This market became more visible today.",
    worthWatching: "Notable today.",
    activeToday: "The topic became more visible in today’s read.",
    attentionMoved: "This market stands out in today’s read.",
    quietNote: "No major shift yet.",
    endingSoonOne: "market is ending soon.",
    endingSoonMany: "markets are ending soon.",
    movesOne: "market changed enough to review.",
    movesMany: "markets changed enough to review.",
    whatChangedTitle: "What changed",
    changedSinceLastBrief: "Changed since last brief",
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
    simpleReadCopy: "Use the probability, volume, timing, and rules together before drawing conclusions.",
    whatMarketAsks: "Market question",
    whatChangedDetail: "What changed",
    quickTake: "Quick take",
    mainTension: "Main tension",
    whatThisMeans: "What this means",
    attentionVsConviction: "Attention vs conviction",
    marketMemory: "Market memory",
    marketRegime: "Market behavior",
    howSerious: "Strength of read",
    whatInfluences: "What to check",
    confidenceLevel: "Confidence level",
    sideConfidenceLow: "Low",
    sideConfidenceMedium: "Medium",
    sideConfidenceHigh: "High",
    influencingFactorsCopy: "News context, public activity, time left, and resolution rules.",
    relatedTopics: "Related topics",
    resolutionRules: "Resolution rules",
    resolutionRulesCopy: "Open the market page and review the official resolution criteria.",
    marketIndicators: "YES / NO balance",
    yesNoBalance: "YES / NO balance",
    side: "Side",
    sideConfidence: "Side read",
    marketLeans: "Market leans",
    sideRead: "Side read",
    marketHeat: "Market heat",
    confirmation: "Read",
    confirmationShort: "Read",
    errorRisk: "Caution",
    riskShort: "Caution",
    timePressure: "Timing",
    marketDepth: "Volume",
    depthShort: "Liveness",
    aiVerdict: "AI verdict",
    aiRead: "AI read",
    todaySummary: "Today",
    mainMarket: "Main market today",
    aiQuickTake: "AI quick take",
    hotCountLabel: "Hot markets",
    endingCountLabel: "Ending soon",
    averageConfirmation: "Market read",
    mainTheme: "Main theme",
    moodQuiet: "Quiet",
    moodActive: "Active",
    moodHeating: "Heating up",
    moodVolatile: "Volatile",
    moodEnding: "Ending soon",
    copied: "Copied",
    appShared: "PulseMarket AI helps you understand what matters on Polymarket.",
    memoryFallback: "Not enough history for comparison yet.",
    heatHot: "Hot",
    heatWarm: "Warm",
    heatCalm: "Calm",
    confirmationWeak: "Weak",
    confirmationMedium: "Medium",
    confirmationStrong: "Strong",
    riskLow: "Low",
    riskMedium: "Medium",
    riskHigh: "High",
    timeEndingSoon: "Ending soon",
    timeHasTime: "Time available",
    timeLongMarket: "Long market",
    depthLive: "Live volume",
    depthMedium: "Medium volume",
    depthWeak: "Weak volume",
    verdictWorthWatching: "Notable",
    verdictCaution: "Caution",
    verdictNotEnoughData: "Not enough data",
    verdictStrongInterest: "Strong interest",
    verdictNotConfident: "Not confident",
    hotMarketsCount: "hot markets",
    endingSoonCount: "ending soon",
    weakConfirmationCount: "limited confidence",
  },
  ru: {
    productLine: "Быстро понять, что важно на Polymarket.",
    researchLabel: "Для анализа · Без сделок",
    botLink: "Бот",
    refresh: "Обновить",
    loadingTitle: "Готовим рыночный обзор",
    loadingStepMarkets: "собираем рынки",
    loadingStepActivity: "сравниваем активность",
    loadingStepChanges: "проверяем изменения",
    loadingStepAnalysis: "готовим короткий разбор",
    apiErrorTitle: "Не удалось загрузить обзор.",
    apiErrorCopy: "Попробуй обновить через несколько секунд.",
    errorRefresh: "Обновить",
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
    eventDesk: "Event intelligence desk",
    topStory: "Главная история",
    storyContext: "Контекст истории",
    storyFrontPage: "Истории рынка сегодня",
    openStory: "Открыть историю",
    linkedMarkets: "Связанные рынки",
    storyConfidence: "Уверенность",
    storySources: "Источники",
    storyChanged: "Что изменилось в истории",
    storyFallback: "Сильной связанной истории пока нет. PulseMarket следит за близкими рынками.",
    pulseKicker: "Пульс дня",
    marketToday: "Рынок сегодня",
    updatedAt: "Обновлено",
    updatedJustNow: "Обновлено только что",
    staleBriefing: "Показываем последний обзор, обновляем в фоне",
    narrativeKicker: "Нарратив дня",
    narrativeTitle: "На что сегодня реагируют рынки.",
    aiBriefingLabel: "AI обзор",
    newsContext: "Новостной фон",
    newsHigh: "Новости: много",
    newsMedium: "Новости: средне",
    newsLow: "Новости: мало",
    officialSource: "Официальный источник",
    socialBuzz: "Социальный фон",
    noStrongNews: "Сильных новостей нет",
    whyMovingNow: "Почему рынок двигается",
    latestImportantNews: "Последняя важная новость",
    sourcesLabel: "Источники",
    officialConfirmation: "Официальное подтверждение",
    whatToVerify: "Что проверить",
    todayReactsTo: "Сегодня рынки реагируют на",
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
    moreSubtitle: "Настройки и объяснение рыночного чтения.",
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
    pulseWorthWatching: "Заметен",
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
    explain: "Разбор",
    save: "Сохранить",
    saved: "Сохранено",
    remove: "Удалить",
    share: "Поделиться",
    publicActivity: "Публичная активность",
    activityLevel: "Уровень активности",
    radarEmpty: "Сейчас нет сильной публичной активности. PulseMarket продолжит отслеживание.",
    radarReason: "Рынок выделяется в слое внимания.",
    radarListTitle: "Ещё рынки с ростом внимания",
    todayEmpty: "Пока собираю картину дня.",
    hotTitle: "Горячие рынки",
    hotSubtitle: "Рынки с сильной текущей активностью.",
    viewAll: "Смотреть все",
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
    marketAttentionRising: "Рынок стал заметнее сегодня.",
    worthWatching: "Заметен сегодня.",
    activeToday: "Тема стала заметнее в сегодняшнем обзоре.",
    attentionMoved: "Рынок выделяется в сегодняшнем обзоре.",
    quietNote: "Без больших изменений.",
    endingSoonOne: "рынок скоро завершится.",
    endingSoonMany: "рынка скоро завершатся.",
    movesOne: "рынок заметно изменился.",
    movesMany: "рынка заметно изменились.",
    whatChangedTitle: "Что изменилось",
    changedSinceLastBrief: "Что изменилось с прошлого обзора",
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
    simpleReadCopy: "Смотри на вероятность, объём, тайминг и правила вместе, прежде чем делать выводы.",
    whatMarketAsks: "О чём рынок",
    whatChangedDetail: "Что изменилось",
    quickTake: "Короткий вывод",
    mainTension: "Главное противоречие",
    whatThisMeans: "Что это значит",
    attentionVsConviction: "Внимание vs убеждённость",
    marketMemory: "Память рынка",
    marketRegime: "Поведение рынка",
    howSerious: "Сила вывода",
    whatInfluences: "Что проверить",
    confidenceLevel: "Уровень уверенности",
    sideConfidenceLow: "Слабая",
    sideConfidenceMedium: "Средняя",
    sideConfidenceHigh: "Сильная",
    influencingFactorsCopy: "Новости, публичная активность, время до завершения и правила разрешения.",
    relatedTopics: "Связанные темы",
    resolutionRules: "Правила разрешения",
    resolutionRulesCopy: "Открой страницу рынка и проверь официальные критерии разрешения.",
    marketIndicators: "Баланс YES / NO",
    yesNoBalance: "Баланс YES / NO",
    side: "Сторона",
    sideConfidence: "Чтение стороны",
    marketLeans: "Рынок склоняется",
    sideRead: "Баланс сторон",
    marketHeat: "Температура",
    confirmation: "Картина",
    confirmationShort: "Картина",
    errorRisk: "Осторожность",
    riskShort: "Осторожно",
    timePressure: "Срок",
    marketDepth: "Объём",
    depthShort: "Объём",
    aiVerdict: "AI вывод",
    aiRead: "AI вывод",
    todaySummary: "Сегодня",
    mainMarket: "Главный рынок дня",
    aiQuickTake: "AI краткий вывод",
    hotCountLabel: "Горячих рынков",
    endingCountLabel: "Скоро завершатся",
    averageConfirmation: "Картина рынка",
    mainTheme: "Главная тема",
    moodQuiet: "Тихо",
    moodActive: "Активно",
    moodHeating: "Разогревается",
    moodVolatile: "Волатильно",
    moodEnding: "Скоро завершение",
    copied: "Скопировано",
    appShared: "PulseMarket AI помогает быстро понять, что важно на Polymarket.",
    memoryFallback: "Пока мало истории для сравнения.",
    heatHot: "Горячий",
    heatWarm: "Тёплый",
    heatCalm: "Спокойный",
    confirmationWeak: "Слабое",
    confirmationMedium: "Среднее",
    confirmationStrong: "Сильное",
    riskLow: "Низкий",
    riskMedium: "Средний",
    riskHigh: "Высокий",
    timeEndingSoon: "Скоро завершение",
    timeHasTime: "Есть время",
    timeLongMarket: "Долгий рынок",
    depthLive: "Объём нормальный",
    depthMedium: "Объём средний",
    depthWeak: "Данных мало",
    verdictWorthWatching: "Заметен",
    verdictCaution: "Осторожно",
    verdictNotEnoughData: "Мало данных",
    verdictStrongInterest: "Сильный интерес",
    verdictNotConfident: "Не выглядит уверенно",
    hotMarketsCount: "горячих рынка",
    endingSoonCount: "скоро завершатся",
    weakConfirmationCount: "уверенности мало",
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

function configureTelegramWebApp() {
  if (!tg) return;
  try {
    if (typeof tg.ready === "function") tg.ready();
    if (typeof tg.expand === "function") tg.expand();
    if (
      typeof tg.isVersionAtLeast === "function" &&
      tg.isVersionAtLeast("7.7") &&
      typeof tg.disableVerticalSwipes === "function"
    ) {
      tg.disableVerticalSwipes();
    }
    if (tg.BackButton) tg.BackButton.hide();
  } catch {
    // Browser preview should keep working even if Telegram WebApp APIs differ.
  }
}

function setTelegramChromeColors(theme = "dark") {
  if (!tg) return;
  const colors = TELEGRAM_CHROME_COLORS[theme] || TELEGRAM_CHROME_COLORS.dark;
  try {
    if (typeof tg.setHeaderColor === "function") tg.setHeaderColor(colors.header);
    if (typeof tg.setBackgroundColor === "function") tg.setBackgroundColor(colors.background);
  } catch {
    // Telegram clients vary; color sync is polish, not a blocker.
  }
}

configureTelegramWebApp();

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
  setTelegramChromeColors(theme);
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

function probabilityNumber(item) {
  if (item && item.probability !== null && item.probability !== undefined) {
    const value = Number(item.probability);
    if (!Number.isNaN(value)) {
      if (value <= 0) return "<1%";
      if (value < 1) return "<1%";
      return `${Math.round(value)}%`;
    }
  }
  const label = String((item && item.probability_label) || "").trim();
  if (label && !/[a-zа-я]/i.test(label)) return label;
  return "n/a";
}

function sidePercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "n/a";
  const bounded = Math.max(0, Math.min(100, Number(value)));
  if (bounded > 0 && bounded < 1) return "<1%";
  return `${Number.isInteger(bounded) ? bounded.toFixed(0) : bounded.toFixed(1)}%`;
}

function sideConfidenceLabel(item) {
  const value = String((item && item.side_confidence) || "low").toLowerCase();
  if (value === "high") return t("sideConfidenceHigh");
  if (value === "medium") return t("sideConfidenceMedium");
  return t("sideConfidenceLow");
}

function dominantSide(item) {
  const side = String((item && item.dominant_side) || "UNKNOWN").toUpperCase();
  return ["YES", "NO", "BALANCED"].includes(side) ? side : "UNKNOWN";
}

function sideBalanceText(item) {
  const side = dominantSide(item);
  if (isRu()) {
    if (side === "YES") return "Рынок склоняется к YES";
    if (side === "NO") return "Рынок склоняется к NO";
    if (side === "BALANCED") return "Стороны близки";
    return "Данных по сторонам мало";
  }
  if (side === "YES") return "Market leans YES";
  if (side === "NO") return "Market leans NO";
  if (side === "BALANCED") return "Both sides are close";
  return "Not enough side data";
}

function marketLeanLine(item) {
  const side = dominantSide(item);
  if (isRu()) {
    if (side === "YES") return "Рынок больше верит в YES.";
    if (side === "NO") return "Рынок больше верит в NO.";
    if (side === "BALANCED") return "Стороны почти равны.";
    return "Данных пока мало.";
  }
  if (side === "YES") return "Market leans YES.";
  if (side === "NO") return "Market leans NO.";
  if (side === "BALANCED") return "Both sides are close.";
  return "Not enough data yet.";
}

function timingLine(item) {
  const key = String((item && item.time_pressure_key) || "");
  if (key === "ending_soon") return isRu() ? "До завершения мало времени." : "Close to resolution.";
  if (key === "has_time") return isRu() ? "Есть время." : "Time remains.";
  return isRu() ? "Долгий рынок." : "Longer market.";
}

function humanRead(item) {
  const outcomeRead = localizedText(item && item.outcome_balance_summary, "");
  if (outcomeRead && !isGenericReason(outcomeRead)) return outcomeRead;
  const direct = localizedText(item && item.side_verdict, "");
  if (direct && !isGenericReason(direct)) return direct;
  const summary = localizedText(item && item.indicator_summary, "");
  if (summary && !isGenericReason(summary)) return summary;
  const side = marketLeanLine(item);
  if (isRu()) {
    if (String((item && item.confirmation_level_key) || "") === "weak") {
      return `${side} Интерес есть, но уверенности мало.`;
    }
    return side;
  }
  if (String((item && item.confirmation_level_key) || "") === "weak") {
    return `${side} Interest is there, confidence is limited.`;
  }
  return side;
}

function shouldUseYesNo(item) {
  return Boolean(item && item.should_use_yes_no !== false && String(item.outcome_type || "binary_yes_no") === "binary_yes_no");
}

function yesNoValues(item) {
  const yes = item && item.yes_probability !== undefined && item.yes_probability !== null
    ? Number(item.yes_probability)
    : Number(item && item.probability);
  const safeYes = Number.isNaN(yes) ? 0 : Math.max(0, Math.min(100, yes));
  const noValue = item && item.no_probability !== undefined && item.no_probability !== null
    ? Number(item.no_probability)
    : 100 - safeYes;
  const safeNo = Number.isNaN(noValue) ? Math.max(0, 100 - safeYes) : Math.max(0, Math.min(100, noValue));
  return { yes: safeYes, no: safeNo };
}

function fallbackOutcomeList(item) {
  const { yes, no } = yesNoValues(item);
  return [
    { label: "YES", short_label: "YES", probability: yes, color_role: "yes" },
    { label: "NO", short_label: "NO", probability: no, color_role: "no" },
  ];
}

function outcomeList(item) {
  const raw = Array.isArray(item && item.display_outcomes) ? item.display_outcomes : [];
  const outcomes = raw
    .map((outcome, index) => ({
      label: String(outcome.label || outcome.short_label || `Outcome ${index + 1}`),
      short_label: String(outcome.short_label || outcome.label || `#${index + 1}`),
      probability: outcome.probability,
      price: outcome.price,
      color_role: String(outcome.color_role || "neutral"),
    }))
    .filter((outcome) => outcome.label.trim());
  if (outcomes.length) return outcomes;
  if (shouldUseYesNo(item)) return fallbackOutcomeList(item);
  return [
    {
      label: isRu() ? "Нет данных" : "No data",
      short_label: "n/a",
      probability: null,
      color_role: "neutral",
    },
  ];
}

function visibleOutcomeList(item, limit = 3) {
  const outcomes = outcomeList(item);
  if (outcomes.length <= limit) return { outcomes, remaining: 0 };
  return { outcomes: outcomes.slice(0, limit), remaining: outcomes.length - limit };
}

function outcomeRoleClass(outcome) {
  const role = String((outcome && outcome.color_role) || "neutral");
  if (role === "yes" || role === "dominant") return "yes";
  if (role === "no") return "no";
  if (role === "runner_up") return "runner";
  return "neutral";
}

function outcomeBalanceLabel(item) {
  if (shouldUseYesNo(item)) return t("yesNoBalance");
  const type = String((item && item.outcome_type) || "");
  if (type === "sports_moneyline") return isRu() ? "Варианты рынка" : "Market outcomes";
  return isRu() ? "Баланс вариантов" : "Outcome balance";
}

function outcomeLeadLine(item) {
  const summary = localizedText(item && item.outcome_balance_summary, "");
  if (summary) return summary;
  const dominant = String((item && item.dominant_outcome_label) || "").trim();
  if (dominant) {
    return isRu() ? `Рынок сильнее склоняется к ${dominant}.` : `Market leans ${dominant}.`;
  }
  return marketLeanLine(item);
}

function outcomeBarSegments(item) {
  const outcomes = outcomeList(item);
  if (!outcomes.length) return [];
  const values = outcomes.map((outcome) => Number(outcome.probability));
  const hasValues = values.some((value) => !Number.isNaN(value) && value > 0);
  const total = hasValues
    ? values.reduce((sum, value) => sum + (Number.isNaN(value) || value < 0 ? 0 : value), 0)
    : outcomes.length;
  return outcomes.map((outcome, index) => {
    const raw = hasValues ? values[index] : 1;
    const value = Number.isNaN(raw) || raw < 0 ? 0 : raw;
    return {
      width: total > 0 ? Math.max(2, (value / total) * 100) : 100 / outcomes.length,
      role: outcomeRoleClass(outcome),
    };
  });
}

function marketHeatScore(item) {
  const pulse = Number((item && item.pulse_score) || 0);
  const volume = Math.log10(Math.max(1, Number((item && (item.volume || item.public_activity)) || 0))) * 7;
  const movement = Math.min(30, Math.abs(Number((item && item.movement) || 0)) * 1.8);
  const regime = String((item && item.market_regime_key) || "");
  const heat = String((item && item.market_heat_key) || "");
  const timing = String((item && item.time_pressure_key) || "");
  return (
    pulse +
    volume +
    movement +
    (heat === "hot" ? 24 : heat === "warm" ? 12 : 0) +
    (regime === "near_resolution" || timing === "ending_soon" ? 10 : 0)
  );
}

function sortByRealHeat(items) {
  return [...(Array.isArray(items) ? items : [])].sort((left, right) => marketHeatScore(right) - marketHeatScore(left));
}

function getMarketVisual(item) {
  const title = String((item && item.title) || "").toLowerCase();
  const category = categoryForItem(item || {});
  if (/israel|syria|gaza|netanyahu|jerusalem|idf/.test(title)) {
    return { icon: "🇮🇱", emoji: "🇮🇱", label: "Israel", category };
  }
  if (/iran|trump|usa|u\\.s\\.|america|white house|congress|biden/.test(title)) {
    return { icon: "🇺🇸", emoji: "🇺🇸", label: "US", category };
  }
  if (/china|xi|beijing/.test(title)) {
    return { icon: "🇨🇳", emoji: "🇨🇳", label: "China", category };
  }
  if (/bitcoin|btc/.test(title)) {
    return { icon: "₿", emoji: "₿", label: "Bitcoin", category };
  }
  if (/ethereum|eth/.test(title)) {
    return { icon: "Ξ", emoji: "Ξ", label: "Ethereum", category };
  }
  if (/ai|openai|nvidia|google|meta|apple/.test(title)) {
    return { icon: "🧠", emoji: "🧠", label: "AI", category };
  }
  const fallback = {
    sports: { icon: "🏟", emoji: "🏟", label: "Sports", category },
    esports: { icon: "🎮", emoji: "🎮", label: "Esports", category },
    politics: { icon: "🏛", emoji: "🏛", label: "Politics", category },
    global: { icon: "🌐", emoji: "🌐", label: "Global", category },
    crypto: { icon: "₿", emoji: "₿", label: "Crypto", category },
    culture: { icon: "◆", emoji: "◆", label: "Culture", category },
  };
  return fallback[category] || { icon: "P", emoji: "P", label: "PulseMarket", category };
}

function marketVisual(item) {
  return getMarketVisual(item).icon;
}

function updatedTimeLabel() {
  try {
    return new Intl.DateTimeFormat(isRu() ? "ru-RU" : "en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(new Date());
  } catch (_error) {
    return "";
  }
}

function briefingUpdatedLabel() {
  const seconds = Number(state.todayMeta && state.todayMeta.updated_ago_seconds);
  if (Number.isFinite(seconds) && seconds >= 0) {
    if (seconds < 60) return t("updatedJustNow");
    const minutes = Math.max(1, Math.round(seconds / 60));
    return isRu()
      ? `${t("updatedAt")} ${minutes} мин назад`
      : `${t("updatedAt")} ${minutes} min ago`;
  }
  const timeLabel = updatedTimeLabel();
  return timeLabel ? `${t("updatedAt")} ${timeLabel}` : t("updatedAt");
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
    "this market is " + "active today",
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
    return isRu() ? "Дедлайн близко; важнее проверить правила разрешения." : "The deadline is close; resolution rules matter more here.";
  }
  if (mood.key === "volatile") {
    return isRu() ? "Вероятность заметно изменилась, и рынок стал заметнее." : "Probability moved enough to make this market stand out.";
  }

  const title = String((item && item.title) || "").toLowerCase();
  const category = categoryForItem(item || {});
  if (/(bitcoin|btc|ethereum|eth|crypto|binance|coinbase)/.test(title) || category === "crypto") {
    return isRu() ? "Крипторынок двигается, поэтому этот сценарий стал заметнее." : "Crypto volatility made this scenario more visible.";
  }
  if (/(iran|israel|trump|election|president|senate|war|diplomacy|china|russia|ukraine)/.test(title) || category === "politics" || category === "global") {
    return isRu() ? "Политическая повестка сделала рынок заметнее." : "Political headlines made this market more visible.";
  }
  if (/(nba|nfl|ufc|soccer|football|tennis|baseball|fifa|playoff|match)/.test(title) || category === "sports") {
    return isRu() ? "Близость события делает рынок чувствительнее к новым данным." : "Event timing makes this market more sensitive to new information.";
  }
  if (/(openai|nvidia|anthropic|robot| ai )/.test(` ${title} `) || category === "ai") {
    return isRu() ? "AI-повестка сделала этот сценарий заметнее." : "The AI news cycle made this scenario more visible.";
  }
  if (Number((item && item.public_activity) || 0) > 0) {
    return isRu() ? "Публичная активность вывела этот рынок в обзор." : "Public activity pushed this market into today’s read.";
  }
  return isRu() ? "Рынок попал в обзор из-за сочетания вероятности, объёма и времени." : "This market made the brief because probability, volume, and timing line up.";
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

function pulseNumber(item) {
  const score = Number((item && item.pulse_score) || 0);
  if (Number.isNaN(score)) return "0";
  return String(Math.round(score));
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
    return { data: [], message: t("apiErrorCopy"), error: true };
  }
}

function clearNode(node) {
  node.classList.remove("skeleton-card", "skeleton-card--structured");
  node.innerHTML = "";
}

function emptyState(message, compact = false) {
  return `<div class="empty-state${compact ? " empty-state--compact" : ""}">${escapeHtml(message || EMPTY_MESSAGE)}</div>`;
}

function errorState(message = t("apiErrorCopy"), compact = false) {
  return `
    <div class="error-state${compact ? " error-state--compact" : ""}">
      <strong>${escapeHtml(t("apiErrorTitle"))}</strong>
      <span>${escapeHtml(message || t("apiErrorCopy"))}</span>
      <button type="button" data-refresh>${escapeHtml(t("errorRefresh"))}</button>
    </div>
  `;
}

function skeletonLines(count = 3) {
  return Array.from({ length: count }, (_, index) => `<span class="skeleton-line skeleton-line--${index + 1}"></span>`).join("");
}

function skeletonPills(count = 2) {
  return `
    <div class="skeleton-pills" aria-hidden="true">
      ${Array.from({ length: count }, (_, index) => `<span class="skeleton-pill${index ? " skeleton-pill--small" : ""}"></span>`).join("")}
    </div>
  `;
}

function skeletonMarketCard(variant = "compact") {
  return `
    <article class="market-card market-card--${variant} skeleton-card skeleton-card--structured">
      ${skeletonLines(3)}
      ${skeletonPills(2)}
      <span class="skeleton-button"></span>
    </article>
  `;
}

function renderLoadingSkeletons() {
  const narrative = document.getElementById("today-narrative");
  const hero = document.getElementById("today-hero");
  const secondary = document.getElementById("today-secondary");
  const radar = document.getElementById("smart-hero");
  const radarList = document.getElementById("radar-list");
  if (narrative) {
    narrative.classList.add("skeleton-card", "skeleton-card--structured");
    narrative.innerHTML = `${skeletonLines(3)}${skeletonPills(2)}`;
  }
  if (hero) {
    hero.classList.add("skeleton-card", "skeleton-card--structured");
    hero.innerHTML = `${skeletonLines(3)}${skeletonPills(2)}<span class="skeleton-button"></span>`;
  }
  if (secondary) {
    secondary.innerHTML = [skeletonMarketCard("secondary"), skeletonMarketCard("secondary")].join("");
  }
  if (radar) {
    radar.classList.add("skeleton-card", "skeleton-card--structured");
    radar.innerHTML = `${skeletonLines(3)}${skeletonPills(2)}<span class="skeleton-button"></span>`;
  }
  if (radarList) {
    radarList.innerHTML = skeletonMarketCard("compact");
  }
  renderDailySnapshot();
  renderTodayExtras();
}

function hideBootLoader() {
  const loader = document.getElementById("app-loading");
  if (!loader || loader.hidden) return;
  loader.classList.add("is-hidden");
  window.setTimeout(() => {
    loader.hidden = true;
  }, state.toggles.reducedAnimations ? 0 : 220);
}

function delay(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function compactTitle(title, limit = 72) {
  const value = String(title || "Untitled market").trim();
  return value.length > limit ? `${value.slice(0, limit - 1).trim()}…` : value;
}

function shortReason(item) {
  if (item && item.quick_take && matchesCurrentLanguage(item.quick_take) && !isGenericReason(item.quick_take)) {
    const sentence = String(item.quick_take).split(".")[0].trim();
    return sentence ? `${sentence}.` : t("selectedToday");
  }
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

function insightStrength(item) {
  const raw = String((item && item.insight_strength) || "");
  const movement = Math.abs(Number((item && item.movement) || 0));
  const activity = Number((item && (item.public_activity || item.volume)) || 0);
  let key = "noticeable";
  if (/convincing|убедительнее/i.test(raw)) key = "convincing";
  else if (/strong|сильн/i.test(raw)) key = "strong";
  else if (/interest|интерес/i.test(raw)) key = "interest";
  else if (/weak|слаб/i.test(raw)) key = "weak";
  else if (movement >= 5 && activity >= 100000) key = "convincing";
  else if (movement >= 3 || activity >= 500000) key = "strong";
  else if (activity >= 100000) key = "interest";
  else if (movement < 1 && activity < 100000) key = "weak";
  const en = {
    weak: "Move is weak",
    interest: "Interest is present",
    noticeable: "More noticeable than usual",
    strong: "Strong attention",
    convincing: "More convincing than usual",
  };
  const ru = {
    weak: "Движение слабое",
    interest: "Есть интерес",
    noticeable: "Рынок заметнее обычного",
    strong: "Сильный интерес",
    convincing: "Движение выглядит убедительнее обычного",
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

function marketRegime(item) {
  const key = String((item && item.market_regime_key) || "").trim();
  const label = String((item && item.market_regime) || "").trim();
  const labels = {
    en: {
      quiet: "Quiet market",
      active: "Market became active",
      short_term_attention: "Short-term attention",
      near_resolution: "Near resolution",
      news_reaction: "News-driven reaction",
      emotional: "Emotional reaction",
      sustained_interest: "Sustained interest",
      weak_confirmation: "Confidence is limited",
      more_confident: "More confident move",
    },
    ru: {
      quiet: "Спокойный рынок",
      active: "Рынок оживился",
      short_term_attention: "Краткосрочное внимание",
      near_resolution: "Перед завершением",
      news_reaction: "Новостная реакция",
      emotional: "Эмоциональная реакция",
      sustained_interest: "Устойчивый интерес",
      weak_confirmation: "Уверенности мало",
      more_confident: "Более уверенное движение",
    },
  };
  if (key && labels[currentLanguage()][key]) return labels[currentLanguage()][key];
  if (label && matchesCurrentLanguage(label)) return label;
  return labels[currentLanguage()].quiet;
}

function keyedLabel(item, field, labels, fallback = "") {
  const key = String((item && item[`${field}_key`]) || "").trim();
  if (key && labels[key]) return t(labels[key]);
  const direct = String((item && item[field]) || "").trim();
  if (direct && matchesCurrentLanguage(direct)) return direct;
  return fallback;
}

function marketHeat(item) {
  return keyedLabel(
    item,
    "market_heat",
    { hot: "heatHot", warm: "heatWarm", calm: "heatCalm" },
    t("heatCalm"),
  );
}

function confirmationLevel(item) {
  return keyedLabel(
    item,
    "confirmation_level",
    { weak: "confirmationWeak", medium: "confirmationMedium", strong: "confirmationStrong" },
    t("confirmationWeak"),
  );
}

function errorRisk(item) {
  return keyedLabel(
    item,
    "error_risk",
    { low: "riskLow", medium: "riskMedium", high: "riskHigh" },
    t("riskMedium"),
  );
}

function timePressure(item) {
  return keyedLabel(
    item,
    "time_pressure",
    { ending_soon: "timeEndingSoon", has_time: "timeHasTime", long_market: "timeLongMarket" },
    marketRegime(item),
  );
}

function marketDepth(item) {
  return keyedLabel(
    item,
    "market_depth",
    { live: "depthLive", medium: "depthMedium", weak: "depthWeak" },
    t("depthWeak"),
  );
}

function aiVerdict(item) {
  return keyedLabel(
    item,
    "ai_verdict",
    {
      worth_watching: "verdictWorthWatching",
      caution: "verdictCaution",
      not_enough_data: "verdictNotEnoughData",
      strong_interest: "verdictStrongInterest",
      not_confident: "verdictNotConfident",
    },
    insightStrength(item),
  );
}

function indicatorSummary(item) {
  const direct = String((item && item.indicator_summary) || "").trim();
  if (direct && matchesCurrentLanguage(direct)) return direct;
  const confirmation = String((item && item.confirmation_level_key) || "weak");
  const risk = String((item && item.error_risk_key) || "medium");
  if (isRu()) {
    if (risk === "high") return "Нужна осторожность: данных для уверенного вывода мало.";
    if (confirmation === "strong") return "Вероятность и объём смотрятся согласованно.";
    return "Интерес есть, но уверенности мало.";
  }
  if (risk === "high") return "Caution is needed because data is limited.";
  if (confirmation === "strong") return "Probability and volume look aligned.";
  return "Interest is there, confidence is limited.";
}

function confidenceValue(item) {
  const key = String((item && item.confirmation_level_key) || "weak");
  if (key === "strong") return 100;
  if (key === "medium") return 62;
  return 28;
}

function depthScoreValue(item) {
  const key = String((item && item.market_depth_key) || "weak");
  if (key === "live") return isRu() ? "Живой" : "Live";
  if (key === "medium") return isRu() ? "Средний" : "Medium";
  return isRu() ? "Слабый" : "Weak";
}

function renderScoreGrid(item) {
  const entries = [
    [t("side"), dominantSide(item), "side"],
    [t("sideConfidence"), sideConfidenceLabel(item), "side-confidence"],
    [t("depthShort"), depthScoreValue(item), "depth"],
    [t("confirmationShort"), confirmationLevel(item), "confirmation"],
    [t("riskShort"), errorRisk(item), "risk"],
    ["Pulse", pulseNumber(item), "pulse"],
  ];
  return `
    <div class="score-grid">
      ${entries
        .map(
          ([label, value, key]) => `
            <div class="score-item score-item--${key}">
              <span class="score-label">${escapeHtml(label)}</span>
              <strong class="score-value">${escapeHtml(value)}</strong>
            </div>
          `,
        )
        .join("")}
    </div>
  `;
}

function probabilityBar(item) {
  const value = Math.max(0, Math.min(100, Number((item && item.probability) || 0)));
  return `
    <div class="probability-bar" aria-hidden="true">
      <span style="width: ${value}%"></span>
    </div>
  `;
}

function confidenceBar(item) {
  return `
    <div class="confidence-bar confidence-bar--${escapeHtml(String((item && item.confirmation_level_key) || "weak"))}" aria-hidden="true">
      <span style="width: ${confidenceValue(item)}%"></span>
    </div>
  `;
}

function scorePills(item) {
  return `
    <div class="score-pills">
      <span class="score-pill score-pill--prob">${escapeHtml(probabilityNumber(item))}</span>
      <span class="score-pill score-pill--meaning">${escapeHtml(probabilityMeaning(item))}</span>
      <span class="pill pill--time">${escapeHtml(timePressure(item))}</span>
    </div>
  `;
}

function renderYesNoStrip(item) {
  const segments = outcomeBarSegments(item);
  return `
    <div class="yes-no-strip">
      <div class="yes-no-strip__labels">
        ${outcomeList(item)
          .slice(0, 3)
          .map((outcome) => `<strong>${escapeHtml(outcome.short_label || outcome.label)} ${escapeHtml(sidePercent(outcome.probability))}</strong>`)
          .join("")}
      </div>
      <div class="side-split-bar" aria-hidden="true">
        ${segments.map((segment) => `<span class="side-split-bar__${escapeHtml(segment.role)}" style="width: ${segment.width}%"></span>`).join("")}
      </div>
      <p class="side-read">${escapeHtml(outcomeLeadLine(item))}</p>
    </div>
  `;
}

function renderYesNoDuel(item, options = {}) {
  const large = Boolean(options.large);
  const { outcomes, remaining } = visibleOutcomeList(item, large ? 3 : 3);
  const segments = outcomeBarSegments(item);
  return `
    <div class="yes-no-duel outcome-duel${large ? " yes-no-duel--large" : ""}${outcomes.length > 2 ? " outcome-duel--multi" : ""}">
      <div class="yes-no-duel__split outcome-duel__split">
        ${outcomes
          .map(
            (outcome) => `
              <div class="yes-no-duel__side outcome-duel__side yes-no-duel__side--${escapeHtml(outcomeRoleClass(outcome))}">
                <span>${escapeHtml(outcome.short_label || outcome.label)}</span>
                <strong>${escapeHtml(sidePercent(outcome.probability))}</strong>
              </div>
            `,
          )
          .join("")}
        ${remaining > 0 ? `<div class="yes-no-duel__side outcome-duel__side yes-no-duel__side--neutral"><span>${escapeHtml(isRu() ? "ещё" : "more")}</span><strong>${remaining}</strong></div>` : ""}
      </div>
      <div class="yes-no-duel__track" aria-hidden="true">
        ${segments.map((segment) => `<span class="yes-no-duel__track-${escapeHtml(segment.role)}" style="width: ${segment.width}%"></span>`).join("")}
      </div>
    </div>
  `;
}

function verdictLine(item) {
  return `
    <div class="verdict-line verdict-line--scorecard">
      <strong>${escapeHtml(indicatorSummary(item))}</strong>
    </div>
  `;
}

function renderMarketScorecard(item, options = {}) {
  const compact = Boolean(options.compact);
  const visual = options.visual || "scorecard";
  if (visual === "duel") {
    return `
      <div class="market-scorecard market-scorecard--duel${compact ? " market-scorecard--compact" : ""}">
        ${renderYesNoDuel(item, { large: !compact })}
      </div>
    `;
  }
  return `
    <div class="market-scorecard${compact ? " market-scorecard--compact" : ""}">
      ${renderYesNoStrip(item)}
      ${scorePills(item)}
      ${probabilityBar(item)}
      ${compact ? "" : renderScoreGrid(item)}
      ${confidenceBar(item)}
      ${verdictLine(item)}
    </div>
  `;
}

function dominantCategory(items) {
  const counts = new Map();
  for (const item of Array.isArray(items) ? items : []) {
    const key = categoryForItem(item);
    counts.set(key, (counts.get(key) || 0) + 1);
  }
  const sorted = Array.from(counts.entries()).sort((left, right) => right[1] - left[1]);
  return sorted[0] ? categoryLabel(sorted[0][0]) : categoryLabel("global");
}

function dominantSideAcross(items) {
  const counts = { YES: 0, NO: 0, BALANCED: 0 };
  for (const item of Array.isArray(items) ? items : []) {
    const side = dominantSide(item);
    if (counts[side] !== undefined) counts[side] += 1;
  }
  if (counts.YES > counts.NO && counts.YES > counts.BALANCED) return "YES";
  if (counts.NO > counts.YES && counts.NO > counts.BALANCED) return "NO";
  if (counts.BALANCED) return "BALANCED";
  return "UNKNOWN";
}

function todayMarketSummary(items, fallback) {
  const markets = Array.isArray(items) ? items : [];
  const theme = dominantCategory(markets);
  const side = dominantSideAcross(markets);
  if (isRu()) {
    if (side === "YES") return `${theme} активнее остальных тем. Большинство горячих рынков склоняются к YES.`;
    if (side === "NO") return `${theme} активнее остальных тем. Большинство горячих рынков склоняются к NO.`;
    if (side === "BALANCED") return `${theme} активнее остальных тем. Несколько сторон идут близко.`;
    return fallback || `${theme} активнее остальных тем.`;
  }
  if (side === "YES") return `${theme} is the most active theme. Most hot markets lean YES.`;
  if (side === "NO") return `${theme} is the most active theme. Most hot markets lean NO.`;
  if (side === "BALANCED") return `${theme} is the most active theme. Several markets are close.`;
  return fallback || `${theme} is the most active theme.`;
}

function averageConfirmation(items) {
  const markets = Array.isArray(items) ? items : [];
  const weights = { weak: 1, medium: 2, strong: 3 };
  if (!markets.length) return confirmationLevel({});
  const average =
    markets.reduce((sum, item) => sum + (weights[String(item.confirmation_level_key || "weak")] || 1), 0) /
    markets.length;
  if (average >= 2.5) return t("confirmationStrong");
  if (average >= 1.6) return t("confirmationMedium");
  return t("confirmationWeak");
}

function todaySummaryStrip(items) {
  const markets = Array.isArray(items) ? items : [];
  const hotCount = markets.filter((item) => String(item.market_heat_key || "") === "hot" || Number(item.pulse_score || 0) >= 75).length;
  const endingCount = markets.filter((item) => String(item.time_pressure_key || "") === "ending_soon").length;
  return `
    <div class="today-dashboard">
      <div class="dashboard-item dashboard-item--hot">
        <b aria-hidden="true">🔥</b>
        <span>${escapeHtml(t("hotCountLabel"))}</span>
        <strong>${hotCount}</strong>
      </div>
      <div class="dashboard-item dashboard-item--time">
        <b aria-hidden="true">◷</b>
        <span>${escapeHtml(t("endingCountLabel"))}</span>
        <strong>${endingCount}</strong>
      </div>
      <div class="dashboard-item dashboard-item--theme">
        <b aria-hidden="true">▦</b>
        <span>${escapeHtml(t("mainTheme"))}</span>
        <strong>${escapeHtml(dominantCategory(markets))}</strong>
      </div>
    </div>
  `;
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
      active: "Интерес есть, но уверенности мало.",
      heating_up: "Тема стала заметнее, но вывод ещё нужно проверять.",
      volatile: "Вероятность заметно изменилась, поэтому рынок выделяется.",
      ending_soon: "Дедлайн близко; правила разрешения особенно важны.",
    }[key] || "Сильного движения пока нет.";
  }
  return {
    quiet: "No strong movement yet.",
    active: "Interest is there, confidence is limited.",
    heating_up: "The topic became more visible, but the read still needs review.",
    volatile: "Probability moved enough to make the market noticeable.",
    ending_soon: "The deadline is close; resolution rules matter more here.",
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
    quick_take: item && item.quick_take,
    simple_read: item && item.simple_read,
    what_happened: item && item.what_happened,
    main_tension: item && item.main_tension,
    what_to_watch: item && (item.what_to_watch || (Array.isArray(item.what_to_check) ? item.what_to_check.join("; ") : item.what_to_check)),
    attention_summary: item && item.attention_summary,
    topic_narrative: item && item.topic_narrative,
    what_this_means: item && item.what_this_means,
    insight_strength: item && item.insight_strength,
    attention_vs_conviction: item && item.attention_vs_conviction,
    confidence_level: item && item.confidence_level,
    resolution_note: item && item.resolution_note,
    category_voice: item && item.category_voice,
    market_memory_summary: item && item.market_memory_summary,
    market_regime: item && item.market_regime,
    market_regime_key: item && item.market_regime_key,
    regime_reason: item && item.regime_reason,
    market_heat: item && item.market_heat,
    market_heat_key: item && item.market_heat_key,
    confirmation_level: item && item.confirmation_level,
    confirmation_level_key: item && item.confirmation_level_key,
    error_risk: item && item.error_risk,
    error_risk_key: item && item.error_risk_key,
    time_pressure: item && item.time_pressure,
    time_pressure_key: item && item.time_pressure_key,
    market_depth: item && item.market_depth,
    market_depth_key: item && item.market_depth_key,
    ai_verdict: item && item.ai_verdict,
    ai_verdict_key: item && item.ai_verdict_key,
    indicator_summary: item && item.indicator_summary,
    side_summary: item && item.side_summary,
    dominant_side: item && item.dominant_side,
    opposite_side: item && item.opposite_side,
    yes_probability: item && item.yes_probability,
    no_probability: item && item.no_probability,
    yes_price: item && item.yes_price,
    no_price: item && item.no_price,
    side_balance: item && item.side_balance,
    side_tension: item && item.side_tension,
    side_confidence: item && item.side_confidence,
    opposite_interest: item && item.opposite_interest,
    side_verdict: item && item.side_verdict,
    side_risk_note: item && item.side_risk_note,
    outcome_type: item && item.outcome_type,
    display_outcomes: Array.isArray(item && item.display_outcomes) ? item.display_outcomes : [],
    dominant_outcome_label: item && item.dominant_outcome_label,
    dominant_outcome_probability: item && item.dominant_outcome_probability,
    runner_up_label: item && item.runner_up_label,
    runner_up_probability: item && item.runner_up_probability,
    outcome_spread: item && item.outcome_spread,
    outcome_balance_summary: item && item.outcome_balance_summary,
    should_use_yes_no: item && item.should_use_yes_no,
    memory_pattern: item && item.memory_pattern,
    changed_since_last_seen: item && item.changed_since_last_seen,
    historical_context: item && item.historical_context,
    news_context: item && item.news_context,
    latest_relevant_news: Array.isArray(item && item.latest_relevant_news) ? item.latest_relevant_news : [],
    related_news: Array.isArray(item && item.related_news) ? item.related_news : [],
    source_count: Number((item && item.source_count) || 0),
    credible_source_count: Number((item && item.credible_source_count) || 0),
    social_heat: item && item.social_heat,
    telegram_heat: item && item.telegram_heat,
    x_heat: item && item.x_heat,
    official_source_signal: Boolean(item && item.official_source_signal),
    official_source_status: item && item.official_source_status,
    news_urgency: item && item.news_urgency,
    why_moving_now: item && item.why_moving_now,
    what_changed_outside_market: item && item.what_changed_outside_market,
    confidence_from_news: item && item.confidence_from_news,
    news_risk_note: item && item.news_risk_note,
    news_count_24h: Number((item && item.news_count_24h) || 0),
    top_news_reason: item && item.top_news_reason,
    source_mix: (item && item.source_mix) || {},
    market_story_id: item && item.market_story_id,
    story_title: item && item.story_title,
    story_context: item && item.story_context,
    news_impact_type: item && item.news_impact_type,
    news_impact_label: item && item.news_impact_label,
    what_changed_in_story: item && item.what_changed_in_story,
    related_markets_count: Number((item && item.related_markets_count) || 0),
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
  const outcomes = outcomeList(item);
  const outcomeLines = outcomes.length
    ? outcomes.slice(0, 5).map((outcome) => `${outcome.short_label || outcome.label}: ${sidePercent(outcome.probability)}`).join("\n")
    : (isRu() ? "Данных по вариантам пока мало" : "Outcome data unavailable");
  return `${item.title || "Polymarket market"}\n${outcomeLines}\n${outcomeLeadLine(item)}\n${humanRead(item)}\n${safeUrl(item.url)}`;
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

function renderMarketCard(item, variant = "compact", options = {}) {
  const normalized = normalizeMarket(item);
  const encoded = encodeURIComponent(JSON.stringify(normalized));
  const visual = getMarketVisual(item);
  const compact = variant === "compact" || variant === "list";
  const showActions = variant !== "list" || options.showActions;
  const removable = Boolean(options.removable);
  const titleLimit = variant === "hero" ? 86 : variant === "list" ? 72 : 78;
  const cardClass = `unified-market-card unified-market-card--${variant}`;
  const { outcomes, remaining } = visibleOutcomeList(item, variant === "list" ? 3 : 3);
  const segments = outcomeBarSegments(item);
  if (variant === "hero" || variant === "analysis") {
    return `
      <div class="${cardClass}" data-explain-market="${encoded}">
        <div class="unified-market-card__topline">
          <span>${escapeHtml(variant === "hero" ? t("mainMarket") : outcomeBalanceLabel(item))}</span>
          <span class="pill pill--time">${escapeHtml(timePressure(item))}</span>
        </div>
        <h3>${escapeHtml(compactTitle(item.title, titleLimit))}</h3>
        ${renderYesNoDuel(item, { large: variant === "hero" })}
        ${renderNewsBadges(normalized)}
        <p class="unified-read">${escapeHtml(humanRead(item))}</p>
        ${renderNewsContextLine(normalized)}
        ${
          variant === "analysis"
            ? ""
            : `<button class="hero-insight-row" type="button" data-explain-market="${encoded}">
                <span>${escapeHtml(t("aiQuickTake"))}: ${escapeHtml(humanRead(item))}</span>
                <strong aria-hidden="true">›</strong>
              </button>`
        }
      </div>
    `;
  }

  return `
    <article class="${cardClass}" data-explain-market="${encoded}">
      <div class="market-avatar" aria-hidden="true" title="${escapeHtml(visual.label)}">${escapeHtml(visual.icon)}</div>
      <div class="unified-market-card__main">
        <h3>${escapeHtml(compactTitle(item.title, titleLimit))}</h3>
        <span>${escapeHtml(timePressure(item))}</span>
      </div>
      <div class="unified-market-card__odds">
        <div class="market-side-buttons outcome-buttons${compact ? " market-side-buttons--compact" : ""}${outcomes.length > 2 ? " outcome-buttons--stack" : ""}">
          ${outcomes
            .map(
              (outcome) => `
                <span class="outcome-button outcome-button--${escapeHtml(outcomeRoleClass(outcome))}">
                  <em>${escapeHtml(outcome.short_label || outcome.label)}</em>
                  <strong>${escapeHtml(sidePercent(outcome.probability))}</strong>
                </span>
              `,
            )
            .join("")}
          ${remaining > 0 ? `<span class="outcome-button outcome-button--neutral"><em>${escapeHtml(isRu() ? "ещё" : "more")}</em><strong>${remaining}</strong></span>` : ""}
        </div>
        <div class="mini-side-bar" aria-hidden="true">
          ${segments.map((segment) => `<i class="mini-side-bar__${escapeHtml(segment.role)}" style="width: ${segment.width}%"></i>`).join("")}
        </div>
      </div>
      <button class="bookmark-action" type="button" data-save-market="${encoded}" aria-label="${escapeHtml(t("save"))}">☆</button>
      <div class="unified-market-card__news">${renderNewsBadges(normalized)}</div>
      ${
        showActions
          ? `<div class="unified-market-card__read">
              <span>${escapeHtml(humanRead(item))}</span>
              ${renderNewsContextLine(normalized)}
            </div>`
          : `<div class="unified-market-card__read unified-market-card__read--compact">${escapeHtml(newsContextLine(normalized))}</div>`
      }
      ${
        showActions
          ? `<div class="action-row action-row--compact">
              <a class="primary-action" href="${escapeHtml(safeUrl(item && item.url))}" target="_blank" rel="noreferrer" data-open-market="${encoded}">${escapeHtml(t("open"))}</a>
              ${
                removable
                  ? `<button type="button" class="soft-action" data-remove-market="${escapeHtml(normalized.id)}">${escapeHtml(t("remove"))}</button>`
                  : `<button type="button" class="soft-action" data-explain-market="${encoded}">${escapeHtml(t("explain"))}</button>`
              }
            </div>`
          : ""
      }
    </article>
  `;
}

function savedCard(item, removable = false) {
  return renderMarketCard(item, "compact", { showActions: true, removable });
}

function normalizedSentence(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[.,:;!?()[\]«»"“”'’\-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function isWeakMemoryText(value) {
  const text = normalizedSentence(value);
  return (
    !text ||
    text.includes("not enough history") ||
    text.includes("мало истории") ||
    text.includes("недостаточно истории")
  );
}

function uniqueAnalysisRows(rows) {
  const seen = new Set();
  const result = [];
  for (const row of rows) {
    const value = localizedText(row.value, "").trim();
    const normalized = normalizedSentence(value);
    if (!normalized || seen.has(normalized)) continue;
    seen.add(normalized);
    result.push({ label: row.label, value });
  }
  return result;
}

function whatToCheckItems(item) {
  const raw = item && item.what_to_watch;
  const source = Array.isArray(raw) ? raw : String(raw || "").split(/[;•\n]/);
  const items = source.map((value) => value.trim()).filter(Boolean);
  if (items.length) return items.slice(0, 3);
  return isRu()
    ? ["правила разрешения", "последние новости", "объём и ликвидность"]
    : ["resolution rules", "latest news", "volume and liquidity"];
}

function renderWhatToCheck(item) {
  return `
    <ul class="check-list">
      ${whatToCheckItems(item).map((value) => `<li>${escapeHtml(value)}</li>`).join("")}
    </ul>
  `;
}

function renderSideAnalysisPanel(item) {
  return `
    <section class="side-panel">
      <div class="indicator-panel__head">
        <span>${escapeHtml(outcomeBalanceLabel(item))}</span>
        <strong>${escapeHtml(item.dominant_outcome_label || dominantSide(item))}</strong>
      </div>
      ${renderYesNoStrip(item)}
      <div class="side-panel__grid">
        ${outcomeList(item)
          .slice(0, 4)
          .map((outcome) => `<span>${escapeHtml(outcome.short_label || outcome.label)} <strong>${escapeHtml(sidePercent(outcome.probability))}</strong></span>`)
          .join("")}
      </div>
      <p>${escapeHtml(localizedText(item.side_tension, outcomeLeadLine(item)))}</p>
      <p>${escapeHtml(localizedText(item.side_verdict, localizedText(item.side_summary, outcomeLeadLine(item))))}</p>
    </section>
  `;
}

function newsLevel(item) {
  const level = String(item.news_urgency || item.confidence_from_news || "low").toLowerCase();
  if (level === "high") return "high";
  if (level === "medium") return "medium";
  return "low";
}

function newsLevelLabel(item) {
  const level = newsLevel(item);
  if (level === "high") return t("newsHigh");
  if (level === "medium") return t("newsMedium");
  return t("newsLow");
}

function newsSourceLabel(item) {
  if (item.official_source_signal) return t("officialSource");
  if (String(item.social_heat || "").toLowerCase() === "high" || String(item.x_heat || "").toLowerCase() === "high") return t("socialBuzz");
  return t("noStrongNews");
}

function newsContextLine(item) {
  const line = localizedText(item.why_moving_now, "");
  if (line && matchesCurrentLanguage(line)) return line;
  const context = localizedText(item.news_context, "");
  if (context && matchesCurrentLanguage(context)) return context;
  return isRu()
    ? "Новостной фон пока не даёт сильного подтверждения."
    : "The news backdrop does not add strong confirmation yet.";
}

function renderNewsBadges(item) {
  const level = newsLevel(item);
  return `
    <div class="news-badges">
      <span class="news-badge news-badge--${escapeHtml(level)}">${escapeHtml(newsLevelLabel(item))}</span>
      <span class="news-badge news-badge--source">${escapeHtml(newsSourceLabel(item))}</span>
    </div>
  `;
}

function renderNewsContextLine(item) {
  return `<p class="news-context-line">${escapeHtml(newsContextLine(item))}</p>`;
}

function hasStrongStory(story) {
  if (!story) return false;
  if (story.is_story_qualified === false) return false;
  const linked = Number(story.related_markets_count || (Array.isArray(story.related_market_ids) ? story.related_market_ids.length : 0));
  if (linked >= 2) return true;
  if (story.official_source_signal) return true;
  const impact = String(story.news_impact_type || "").toLowerCase();
  return impact === "official_confirmed" || (impact === "multiple_sources" && Number(story.source_count || 0) >= 2);
}

function storyLinkedMarkets(story) {
  return Array.isArray(story && story.linked_markets) ? story.linked_markets.map(normalizeMarket) : [];
}

function storySourceBadge(story) {
  if (!story) return t("noStrongNews");
  if (story.official_source_signal) return t("officialSource");
  if (Number(story.source_count || 0) >= 2) return t("storySources");
  return storyImpactLabel(story);
}

function storyImpactLabel(story) {
  const direct = localizedText(story && story.news_impact_label, "");
  if (direct) return direct;
  const type = String((story && story.news_impact_type) || "").toLowerCase();
  if (type === "official_confirmed") return t("officialSource");
  if (type === "multiple_sources") return t("newsMedium");
  if (type === "social_only") return t("socialBuzz");
  return t("noStrongNews");
}

function storySummaryLine(story) {
  if (!story) return t("storyFallback");
  const direct = localizedText(story.why_it_matters, "");
  if (direct) return direct;
  const linked = Number(story.related_markets_count || (Array.isArray(story.related_market_ids) ? story.related_market_ids.length : 0));
  if (isRu()) {
    if (linked >= 2) return `История объединяет ${linked} рынков. ${storyImpactLabel(story)}.`;
    if (story.official_source_signal) return "Одиночный рынок, но есть официальный источник.";
    return t("storyFallback");
  }
  if (linked >= 2) return `This story links ${linked} markets. ${storyImpactLabel(story)}.`;
  if (story.official_source_signal) return "Single-market story with official-source context.";
  return t("storyFallback");
}

function storyChangedLine(story) {
  const direct = localizedText(story && story.what_changed_in_story, "");
  if (direct) return direct;
  const linked = Number(story && story.related_markets_count || 0);
  if (isRu()) {
    if (story && story.official_source_signal) return "Появился официальный контекст по истории.";
    if (linked >= 2) return "Несколько связанных рынков попали в одну историю.";
    return "История пока формируется.";
  }
  if (story && story.official_source_signal) return "Official context entered the story.";
  if (linked >= 2) return "Several related markets now sit inside one story.";
  return "The story is still forming.";
}

function renderStoryCard(story, variant = "compact") {
  if (!hasStrongStory(story)) return "";
  const markets = storyLinkedMarkets(story);
  const mainMarket = markets[0];
  const encoded = mainMarket ? encodeURIComponent(JSON.stringify(mainMarket)) : "";
  const visual = getMarketVisual(mainMarket || { category: story.primary_category, title: story.story_title });
  const linkedCount = Number(story.related_markets_count || markets.length || 0);
  const cardClass = `story-brief-card story-brief-card--${variant}`;
  const preview = markets
    .slice(0, variant === "hero" ? 3 : 2)
    .map(
      (market) => `
        <div class="story-linked-market" data-explain-market="${encodeURIComponent(JSON.stringify(market))}">
          <span>${escapeHtml(compactTitle(market.title, 58))}</span>
          <strong>${escapeHtml(outcomeLeadLine(market))}</strong>
        </div>
      `,
    )
    .join("");
  return `
    <article class="${cardClass}" ${encoded ? `data-explain-market="${encoded}"` : ""}>
      <div class="story-brief-card__top">
        <span class="market-avatar" aria-hidden="true">${escapeHtml(visual.icon)}</span>
        <div>
          <em>${escapeHtml(variant === "hero" ? t("topStory") : categoryLabel(story.primary_category))}</em>
          <h3>${escapeHtml(story.story_title || t("storyFrontPage"))}</h3>
        </div>
      </div>
      <p>${escapeHtml(storySummaryLine(story))}</p>
      <div class="story-metadata-row">
        <span>${escapeHtml(storySourceBadge(story))}</span>
        <span>${escapeHtml(linkedCount)} ${escapeHtml(t("linkedMarkets"))}</span>
        <span>${escapeHtml(story.confidence_level || "low")}</span>
      </div>
      ${preview ? `<div class="story-linked-list">${preview}</div>` : ""}
      ${
        variant === "hero" && mainMarket
          ? `<div class="story-main-market">
              <span>${escapeHtml(t("mainMarket"))}</span>
              ${renderYesNoDuel(mainMarket, { large: true })}
              <p>${escapeHtml(humanRead(mainMarket))}</p>
            </div>`
          : ""
      }
      ${
        mainMarket
          ? `<button class="hero-insight-row" type="button" data-explain-market="${encoded}">
              <span>${escapeHtml(t("openStory"))}</span>
              <strong aria-hidden="true">›</strong>
            </button>`
          : ""
      }
    </article>
  `;
}

function hasMarketStory(item) {
  const normalized = item || {};
  const linked = Number(normalized.related_markets_count || 0);
  const impact = String(normalized.news_impact_type || "").toLowerCase();
  return Boolean(
    normalized.story_title &&
    (linked >= 2 || normalized.official_source_signal || impact === "official_confirmed" || impact === "multiple_sources"),
  );
}

function renderStoryContextPanel(item) {
  if (!hasMarketStory(item)) return "";
  const rows = uniqueAnalysisRows([
    { label: t("storyChanged"), value: storyChangedLine(item) },
    { label: t("newsContext"), value: storySummaryLine(item) },
    { label: t("officialConfirmation"), value: localizedText(item.official_source_status, newsSourceLabel(item)) },
    { label: t("linkedMarkets"), value: `${item.related_markets_count || 1}` },
  ]);
  return `
    <section class="story-context-panel">
      <div class="mini-panel__header">
        <h3>${escapeHtml(t("storyContext"))}</h3>
      </div>
      <strong>${escapeHtml(item.story_title)}</strong>
      ${rows.map((row) => `<p><span>${escapeHtml(row.label)}</span>${escapeHtml(row.value)}</p>`).join("")}
    </section>
  `;
}

function openExplain(item) {
  const normalized = normalizeMarket(item);
  state.lastExplained = normalized;
  const sheet = document.getElementById("explain-sheet");
  const title = document.getElementById("explain-title");
  const body = document.getElementById("explain-body");
  const actions = document.getElementById("explain-actions");
  const topics = Array.isArray(normalized.related_topics) && normalized.related_topics.length
    ? normalized.related_topics.map(topicLabel).join(", ")
    : categoryLabel(normalized.category || "global");
  const memoryText = localizedText(normalized.market_memory_summary, t("memoryFallback"));
  const memoryIsWeak = isWeakMemoryText(memoryText);
  const rows = uniqueAnalysisRows([
    { label: t("quickTake"), value: localizedText(normalized.quick_take, normalized.why || shortReason(normalized)) },
    { label: t("whyMovingNow"), value: newsContextLine(normalized) },
    { label: t("latestImportantNews"), value: localizedText(normalized.what_changed_outside_market, "") },
    { label: t("whatThisMeans"), value: localizedText(normalized.what_this_means, indicatorSummary(normalized)) },
    { label: t("mainTension"), value: localizedText(normalized.main_tension, localizedText(normalized.attention_vs_conviction, indicatorSummary(normalized))) },
    { label: t("attentionVsConviction"), value: localizedText(normalized.attention_vs_conviction, "") },
    { label: t("officialConfirmation"), value: localizedText(normalized.official_source_status, newsSourceLabel(normalized)) },
    { label: t("relatedTopics"), value: topics },
    { label: t("resolutionRules"), value: localizedText(normalized.resolution_note, t("resolutionRulesCopy")) },
  ]);

  title.textContent = normalized.title;
  body.innerHTML = `
    ${renderMarketCard(normalized, "analysis")}
    ${renderStoryContextPanel(normalized)}
    <div class="detail-list">
      <div>
        <span>${escapeHtml(t("newsContext"))}</span>
        <strong>${escapeHtml(newsContextLine(normalized))}</strong>
      </div>
      <div>
        <span>${escapeHtml(t("whatInfluences"))}</span>
        ${renderWhatToCheck(normalized)}
      </div>
      ${rows
        .map(
          (row) => `
            <div>
              <span>${escapeHtml(row.label)}</span>
              <strong>${escapeHtml(row.value)}</strong>
            </div>
          `,
        )
        .join("")}
      <p class="analysis-note">${escapeHtml(memoryIsWeak ? t("memoryFallback") : memoryText)}</p>
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

  if (state.loading.today || state.loading.hot || state.loading.moves) {
    changed.classList.add("skeleton-card", "skeleton-card--structured");
    moodTarget.classList.add("skeleton-card", "skeleton-card--structured");
    changed.innerHTML = `${skeletonLines(3)}${skeletonPills(1)}`;
    moodTarget.innerHTML = `${skeletonLines(2)}${skeletonPills(1)}`;
    return;
  }

  const allMarkets = [...state.today, ...state.hot, ...state.moves];
  const notes = [];
  if (Array.isArray(state.todayMeta.changed_since_last_brief)) {
    notes.push(...state.todayMeta.changed_since_last_brief.filter((item) => matchesCurrentLanguage(item)));
  }
  if (Array.isArray(state.todayMeta.what_changed)) {
    notes.push(...state.todayMeta.what_changed.filter((item) => matchesCurrentLanguage(item)));
  }
  if (Array.isArray(state.todayMeta.news_themes)) {
    notes.push(
      ...state.todayMeta.news_themes
        .slice(0, 2)
        .map((theme) => `📰 ${theme.theme}: ${theme.latest_news || theme.why_it_matters || t("noStrongNews")}`),
    );
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
      <h3>${escapeHtml(t("changedSinceLastBrief"))}</h3>
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

  if (state.loading.today) {
    target.classList.add("skeleton-card", "skeleton-card--structured");
    target.innerHTML = `${skeletonLines(3)}${skeletonPills(2)}`;
    return;
  }
  if (state.errors.today) {
    target.innerHTML = errorState(t("apiErrorCopy"), true);
    return;
  }

  const category = selectedCategory();
  const moodCategories = rankedMoodCategories([...state.today, ...state.hot, ...state.moves]);
  const topCategory = category !== "all" ? category : (moodCategories[0] && moodCategories[0][0]) || "other";
  const apiHeadline = localizedText(state.todayMeta.narrative, "");
  const apiInterpretation = localizedText(state.todayMeta.interpretation, "");
  const topStory = hasStrongStory(state.todayMeta.top_story) ? state.todayMeta.top_story : null;
  const headline = apiHeadline || editorialHeadline(topCategory);
  const changes = moodCategories
    .slice(0, 3)
    .map(([itemCategory, mood]) => editorialChange(itemCategory, mood.key));
  const visibleToday = filterBySelectedCategory(state.today);

  target.innerHTML = `
    <div class="daily-brief-card__top">
      <span class="section-kicker">${escapeHtml(topStory ? t("eventDesk") : t("pulseKicker"))}</span>
      <span class="updated-pill">${escapeHtml(briefingUpdatedLabel())}</span>
    </div>
    <h3>${escapeHtml(topStory ? topStory.story_title : t("marketToday"))}</h3>
    <p>${escapeHtml(topStory ? storySummaryLine(topStory) : todayMarketSummary(visibleToday, apiInterpretation || headline))}</p>
    ${state.todayMeta.is_stale ? `<p class="briefing-status">${escapeHtml(t("staleBriefing"))}</p>` : ""}
    ${renderNewsThemeStrip()}
    ${todaySummaryStrip(visibleToday)}
  `;
}

function renderNewsThemeStrip() {
  const themes = Array.isArray(state.todayMeta.news_themes) ? state.todayMeta.news_themes.slice(0, 3) : [];
  if (!themes.length) return "";
  return `
    <div class="news-theme-strip" aria-label="${escapeHtml(t("todayReactsTo"))}">
      ${themes
        .map(
          (theme) => `
            <span>
              <em>${escapeHtml(theme.theme || t("newsContext"))}</em>
              <strong>${escapeHtml(theme.confidence || "low")}</strong>
            </span>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderToday(payload) {
  state.loading.today = false;
  state.errors.today = Boolean(payload && payload.error);
  state.today = dataFrom(payload);
  state.todayMeta = {
    narrative: payload && payload.narrative,
    interpretation: payload && payload.interpretation,
    what_changed: Array.isArray(payload && payload.what_changed) ? payload.what_changed : [],
    changed_since_last_brief: Array.isArray(payload && payload.changed_since_last_brief) ? payload.changed_since_last_brief : [],
    category_summaries: (payload && payload.category_summaries) || {},
    news_themes: Array.isArray(payload && payload.news_themes) ? payload.news_themes : [],
    top_story: hasStrongStory(payload && payload.top_story) ? payload.top_story : null,
    story_clusters: Array.isArray(payload && payload.story_clusters)
      ? payload.story_clusters.filter(hasStrongStory)
      : [],
    is_cached: Boolean(payload && payload.is_cached),
    is_stale: Boolean(payload && payload.is_stale),
    generated_at: payload && payload.generated_at,
    updated_ago_seconds: payload && payload.updated_ago_seconds,
    refresh_status: payload && payload.refresh_status,
  };
  const hero = document.getElementById("today-hero");
  const secondary = document.getElementById("today-secondary");
  clearNode(hero);
  secondary.innerHTML = "";

  const visibleToday = filterBySelectedCategory(state.today);
  renderNarrative();
  if (state.errors.today) {
    hero.innerHTML = errorState(payload && payload.message);
    renderDailySnapshot();
    return;
  }
  if (!visibleToday.length) {
    hero.innerHTML = emptyState(t("todayEmpty"));
    return;
  }

  if (state.todayMeta.top_story) {
    hero.innerHTML = renderStoryCard(state.todayMeta.top_story, "hero");
    secondary.innerHTML = state.todayMeta.story_clusters
      .filter((story) => story.story_cluster_id !== state.todayMeta.top_story.story_cluster_id)
      .slice(0, 2)
      .map((story) => renderStoryCard(story, "compact"))
      .join("");
  } else {
    hero.innerHTML = renderMarketCard(visibleToday[0], "hero");
    secondary.innerHTML = "";
  }
}

function renderRadar(payload) {
  state.loading.radar = false;
  state.errors.radar = Boolean(payload && payload.error);
  state.radar = dataFrom(payload);
  const hero = document.getElementById("smart-hero");
  const list = document.getElementById("radar-list");
  clearNode(hero);
  list.innerHTML = "";

  const visibleRadar = filterBySelectedCategory(state.radar);
  if (state.errors.radar) {
    hero.innerHTML = errorState(payload && payload.message, true);
    return;
  }
  if (!visibleRadar.length) {
    hero.innerHTML = emptyState(t("radarEmpty"), true);
    return;
  }

  hero.innerHTML = renderMarketCard(visibleRadar[0], "compact", { showActions: true });

  const rest = visibleRadar.slice(1, 5);
  if (rest.length) {
    list.innerHTML = `
      <h3 class="list-title">${escapeHtml(t("radarListTitle"))}</h3>
      ${rest.map((item) => renderMarketCard(item, "list")).join("")}
    `;
  }
}

function renderHot(payload) {
  state.loading.hot = false;
  state.errors.hot = Boolean(payload && payload.error);
  state.hot = dataFrom(payload);
}

function renderMoves(payload) {
  state.loading.moves = false;
  state.errors.moves = Boolean(payload && payload.error);
  state.moves = dataFrom(payload).filter((item) => Math.abs(Number(item.movement || 0)) >= 5);
}

function renderSearch(payload) {
  state.searchResults = dataFrom(payload);
  state.searchMeta = { summary: payload && payload.summary };
  const target = document.getElementById("search-results");
  if (payload && payload.error) {
    target.innerHTML = errorState(payload.message, true);
    return;
  }
  const localizedSummary = localizedText(
    state.searchMeta.summary,
    state.searchResults[0] ? editorialReason(state.searchResults[0]) : "",
  );
  const summary = localizedSummary
    ? `<div class="search-summary"><span>${escapeHtml(t("searchContextSummary"))}</span><strong>${escapeHtml(localizedSummary)}</strong></div>`
    : "";
  target.innerHTML = state.searchResults.length
    ? summary + state.searchResults.slice(0, 5).map((item) => renderMarketCard(item, "compact", { showActions: true })).join("")
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

  const mainTodayId = marketId(filterBySelectedCategory(state.today)[0] || {});
  const hotCards = sortByRealHeat(filterBySelectedCategory(state.hot))
    .filter((item) => marketId(item) !== mainTodayId)
    .slice(0, 5)
    .map((item) => renderMarketCard(item, "list"))
    .join("");
  const movesCards = sortByRealHeat(filterBySelectedCategory(state.moves)).slice(0, 3).map((item) => renderMarketCard(item, "list")).join("");
  const hotBody = state.loading.hot
    ? `<div class="market-row-list">${[skeletonMarketCard(), skeletonMarketCard()].join("")}</div>`
    : state.errors.hot
      ? errorState(t("apiErrorCopy"), true)
      : `<div class="market-row-list">${hotCards || emptyState(t("hotEmpty"), true)}</div>`;
  const movesBody = state.loading.moves
    ? `<div class="compact-list">${skeletonMarketCard()}</div>`
    : state.errors.moves
      ? errorState(t("apiErrorCopy"), true)
      : `<div class="compact-list">${movesCards || emptyState(t("movesEmpty"), true)}</div>`;

  existing.innerHTML = `
    <div class="subsection-heading">
      <h3>${escapeHtml(t("hotTitle"))}</h3>
      <span>${escapeHtml(t("viewAll"))}</span>
    </div>
    ${hotBody}
    <div class="subsection-heading subsection-heading--spaced">
      <h3>${escapeHtml(t("movesTitle"))}</h3>
      <span>${escapeHtml(state.moves.length ? t("movesSubtitle") : t("movesEmpty"))}</span>
    </div>
    ${movesBody}
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

async function refreshDashboard(options = {}) {
  state.loading = { today: true, radar: true, hot: true, moves: true };
  state.errors = {};
  renderLoadingSkeletons();
  renderSaved();

  const tasks = [
    loadJson("/api/today").then((payload) => {
      renderToday(payload);
      renderDailySnapshot();
    }),
    loadJson("/api/smart-money/active").then(renderRadar),
    loadJson("/api/markets/hot").then((payload) => {
      renderHot(payload);
      renderTodayExtras();
      renderDailySnapshot();
    }),
    loadJson("/api/markets/moves").then((payload) => {
      renderMoves(payload);
      renderTodayExtras();
      renderDailySnapshot();
    }),
  ];

  if (options.initial) {
    const firstSettled = Promise.race(tasks.map((task) => task.catch(() => null)));
    await Promise.all([delay(BOOT_LOADING_MIN_MS), firstSettled]);
    hideBootLoader();
  }

  await Promise.allSettled(tasks);
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

    const saveElement = target.closest("[data-save-market]");
    const savePayload = saveElement instanceof HTMLElement ? saveElement.getAttribute("data-save-market") : null;
    if (savePayload) {
      saveMarket(JSON.parse(decodeURIComponent(savePayload)));
      return;
    }

    const removeElement = target.closest("[data-remove-market]");
    const removeId = removeElement instanceof HTMLElement ? removeElement.getAttribute("data-remove-market") : null;
    if (removeId) {
      removeSaved(removeId);
      return;
    }

    const openElement = target.closest("[data-open-market]");
    const openPayload = openElement instanceof HTMLElement ? openElement.getAttribute("data-open-market") : null;
    if (openPayload) {
      addRecentMarket(JSON.parse(decodeURIComponent(openPayload)));
      return;
    }

    const explainElement = target.closest("[data-explain-market]");
    const explainPayload = explainElement instanceof HTMLElement ? explainElement.getAttribute("data-explain-market") : null;
    if (explainPayload) {
      openExplain(JSON.parse(decodeURIComponent(explainPayload)));
      return;
    }

    const shareElement = target.closest("[data-share-market]");
    const sharePayload = shareElement instanceof HTMLElement ? shareElement.getAttribute("data-share-market") : null;
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
renderLoadingSkeletons();
refreshDashboard({ initial: true });
