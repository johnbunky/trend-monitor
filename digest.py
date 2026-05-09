"""
Digest generator — uses Groq (llama-3.1-8b-instant, free tier)
to write a concise daily digest from the top scored items.
"""

import os
import httpx
import json
from datetime import datetime, timezone

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"

SYSTEM_PROMPT = """You are a sharp indie game trend analyst.
Your job: read a list of trending posts/games and write a concise daily digest.

Rules:
- Write in a direct, enthusiastic but not hype-y tone
- Lead with the most interesting signal
- Group by theme if possible (game feel, mechanics, new releases)
- Each item: one sentence max — what it is + why it matters to an indie dev
- End with one "takeaway" sentence: what pattern do you see today?
- Use plain text only (no markdown headers, no bullet asterisks — just clean readable text)
- Keep total length under 600 words
- Format for Telegram: use emoji sparingly but effectively"""

USER_TEMPLATE = """\
Today's top {n} indie game trend signals. Keywords we track: {keywords}.

ITEMS:
{items_block}

Write the daily digest."""


def generate_digest(items: list[dict], keywords: list[str]) -> str:
    if not items:
        return "📭 No trend signals found today."

    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        # Fallback: simple formatted list if no API key
        return _fallback_digest(items)

    items_block = _format_items(items)
    user_msg = USER_TEMPLATE.format(
        n=len(items),
        keywords=", ".join(keywords),
        items_block=items_block,
    )

    try:
        with httpx.Client(timeout=30) as client:
            r = client.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_msg},
                    ],
                    "max_tokens": 700,
                    "temperature": 0.7,
                },
            )
            r.raise_for_status()
            ai_text = r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Groq error: {e}")
        return _fallback_digest(items)

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"🎮 *Trend Monitor — {date_str}*\n\n{ai_text}"


def _format_items(items: list[dict]) -> str:
    lines = []
    for i, item in enumerate(items, 1):
        desc = item.get("description", "")[:150].strip()
        lines.append(
            f"{i}. [{item['source']}] {item['title']}\n"
            f"   URL: {item['url']}\n"
            f"   {desc}"
        )
    return "\n\n".join(lines)


def _fallback_digest(items: list[dict]) -> str:
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [f"🎮 Trend Monitor — {date_str}\n"]
    for item in items:
        lines.append(f"• [{item['source']}] {item['title']}\n  {item['url']}")
    return "\n".join(lines)
