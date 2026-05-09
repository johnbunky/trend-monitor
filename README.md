# Trend Monitor

Daily indie game feel trend digest — scrapes Itch.io, Reddit, Hacker News, and IndieDB, scores by velocity, summarises with Groq AI, sends to Telegram every morning.

## Sources

| Source | What it finds |
|---|---|
| Itch.io | New + top-rated games matching keywords |
| Reddit r/Unity2D, r/love2d, r/gamedev | Technical breakthroughs in game feel |
| Hacker News | Show HN posts, dev discussions |
| IndieDB | Pure indie releases and news |

## Keywords tracked

- kinetic satisfaction · minimalist physics · emergent storytelling
- atmospheric indie · co-op mechanics · game feel · juice · game jam

## Setup

### 1. Secrets — add these in GitHub → Settings → Secrets → Actions

| Secret | Where to get it |
|---|---|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) — free |
| `REDDIT_CLIENT_ID` | [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) → create "script" app |
| `REDDIT_CLIENT_SECRET` | same page |
| `TELEGRAM_BOT_TOKEN` | Message [@BotFather](https://t.me/BotFather) → `/newbot` |
| `TELEGRAM_CHAT_ID` | Message [@userinfobot](https://t.me/userinfobot) to get your ID |

### 2. Enable the workflow

Push to main — the Action runs automatically at **08:00 UTC** daily.
You can also trigger it manually from the Actions tab → "Daily Trend Monitor" → Run workflow.

### 3. Local testing

```bash
cp .env.example .env
# fill in your keys
pip install -r requirements.txt
python -c "from dotenv import load_dotenv; load_dotenv()"  # optional
python monitor.py
```

Or with env vars inline:
```bash
GROQ_API_KEY=... TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=... \
REDDIT_CLIENT_ID=... REDDIT_CLIENT_SECRET=... python monitor.py
```

## Scoring

Items are ranked by **velocity**: engagement (upvotes + comments) weighted by recency.
Items less than 12h old score highest. The top 8 are passed to Groq for the digest.

## Model

`llama-3.1-8b-instant` via Groq — free tier, fast, no credit card needed.
To switch model, edit `MODEL` in `digest.py`.

## Related

Built as a companion to [terminal_ai](https://github.com/johnbunky/terminal_ai) — a universal AI CLI in Lua.
