#!/usr/bin/env python3
"""
Weekly summary — reads last 7 daily reports from reports/,
generates a week-in-review digest via Groq, sends to Telegram.
"""

import os
import glob
import asyncio
from datetime import datetime, timezone
from digest import GROQ_URL, MODEL
from telegram_bot import send_message
import httpx

WEEKLY_SYSTEM_PROMPT = """You are a sharp indie game trend analyst writing a weekly review.
You will receive 7 daily digests. Your job: find the patterns across the week.

Rules:
- What themes kept appearing across multiple days? Those are real trends.
- What was a one-day spike vs a sustained signal?
- Highlight 2-3 recurring themes with examples from specific days
- Call out one "signal of the week" — the single most interesting development
- End with one actionable insight for an indie dev: what should they be paying attention to?
- Plain text, no markdown headers, use emoji sparingly
- Keep it under 500 words
- Format for Telegram"""


async def main():
    print("📚 Loading weekly reports...")
    reports = load_reports()

    if not reports:
        print("⚠️  No reports found in reports/")
        return

    print(f"  Found {len(reports)} reports")
    summary = generate_weekly(reports)

    print("📤 Sending weekly summary to Telegram...")
    await send_message(summary)
    print("✅ Done!")


def load_reports() -> dict[str, str]:
    files = sorted(glob.glob("reports/*.txt"))[-7:]  # last 7
    reports = {}
    for f in files:
        date = os.path.basename(f).replace(".txt", "")
        with open(f) as fh:
            reports[date] = fh.read()
    return reports


def generate_weekly(reports: dict[str, str]) -> str:
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        return _fallback(reports)

    block = "\n\n".join(
        f"=== {date} ===\n{text}" for date, text in reports.items()
    )

    user_msg = f"Here are the last {len(reports)} daily indie game trend digests:\n\n{block}\n\nWrite the weekly review."

    try:
        with httpx.Client(timeout=40) as client:
            r = client.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": WEEKLY_SYSTEM_PROMPT},
                        {"role": "user", "content": user_msg},
                    ],
                    "max_tokens": 700,
                    "temperature": 0.7,
                },
            )
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Groq error: {e}")
        return _fallback(reports)

    week_start = min(reports.keys())
    week_end = max(reports.keys())
    return f"📊 *Weekly Trend Review — {week_start} → {week_end}*\n\n{text}"


def _fallback(reports: dict[str, str]) -> str:
    dates = ", ".join(reports.keys())
    return f"📊 Weekly Trend Review\nReports collected: {dates}\n\n(Groq unavailable — check API key)"


if __name__ == "__main__":
    asyncio.run(main())
