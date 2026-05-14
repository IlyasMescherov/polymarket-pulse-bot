# PulseMarket Bot Demo Script

## Submission facts

- Telegram handle: [@PulseMarketAIBot](https://t.me/PulseMarketAIBot)
- GitHub repo: [https://github.com/IlyasMescherov/polymarket-pulse-bot](https://github.com/IlyasMescherov/polymarket-pulse-bot)
- Landing page: [http://2.26.80.27:8080](http://2.26.80.27:8080)
- Production health: [http://2.26.80.27:8080/health](http://2.26.80.27:8080/health)
- Status: Live MVP

## Safety note

Do not show private `.env`, tokens, server terminal, personal chats, or unrelated windows in the demo.

PulseMarket AI is analytics only:

- No trading
- No wallet management
- No deposits
- No private keys
- No custody
- No financial advice

Builder code is prepared for future official trading integration, but the current MVP uses public Polymarket market data only.

## 45-second demo video

### 0-5 sec: Start

Open [@PulseMarketAIBot](https://t.me/PulseMarketAIBot) and send:

```text
/start
```

### 5-10 sec: Main menu

Show the main menu in English mode if possible.

Highlight:

- Analytics only
- No wallets
- No deposits
- No trading

### 10-17 sec: Hot Markets

Tap:

```text
Hot
```

Show a market card with:

- Probability
- Volume
- Pulse Score
- Market Health
- Risk flags if present

### 17-21 sec: Today's Pulse

Tap:

```text
Today's Pulse
```

Show the ranked daily discovery card.

### 21-27 sec: Search

Use Search and type:

```text
bitcoin
```

Show the search result cards.

### 27-31 sec: Open Polymarket link

Tap:

```text
Open
```

Show that the bot sends a direct Polymarket market link.

### 31-35 sec: Resolution Explainer and Why It Moved

Tap:

```text
Rules
```

Then tap:

```text
Why it moved
```

Show the resolution guidance and movement explanation.

### 35-39 sec: Inline search

In any Telegram chat field, type:

```text
@PulseMarketAIBot bitcoin
```

Show inline results.

### 39-43 sec: Admin stats

Send:

```text
/admin_stats
```

Show the admin stats screen. Crop the screenshot or recording so no private chats are visible.

### 43-45 sec: Final screen

Show:

```text
Telegram: @PulseMarketAIBot
GitHub: https://github.com/IlyasMescherov/polymarket-pulse-bot
Landing: http://2.26.80.27:8080
Health: http://2.26.80.27:8080/health
Status: Live MVP
```
