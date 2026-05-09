#!/usr/bin/env python3
"""
Trend Monitor — daily indie game feel digest
Runs via GitHub Actions, sends to Telegram.
"""

import asyncio
import sys
from sources.itchio import fetch_itchio
from sources.reddit import fetch_reddit
from sources.hackernews import fetch_hackernews
from sources.indiedb import fetch_indiedb
from scorer import score_items
from digest import generate_digest
from telegram_bot import send_message

KEYWORDS = [
    "kinetic satisfaction",
    "minimalist physics",
    "emergent storytelling",
    "atmospheric indie",
    "co-op mechanics",
    "game feel",
    "juice",
    "game jam",
]

TOP_N = 8  # items passed to the AI digest


async def main():
    print("🔍 Fetching from all sources...")

    results = []

    for fetcher, name in [
        (fetch_itchio, "Itch.io"),
        (fetch_reddit, "Reddit"),
        (fetch_hackernews, "Hacker News"),
        (fetch_indiedb, "IndieDB"),
    ]:
        try:
            items = await fetcher(KEYWORDS)
            print(f"  ✅ {name}: {len(items)} items")
            results += items
        except Exception as e:
            print(f"  ⚠️  {name} failed: {e}", file=sys.stderr)

    print(f"\n📦 Total raw items: {len(results)}")

    if not results:
        msg = "📭 *Trend Monitor* — no items found today across all sources. Will retry tomorrow."
        await send_message(msg)
        return

    scored = score_items(results)
    top = scored[:TOP_N]

    print(f"🏆 Top {len(top)} items selected, generating digest...")
    digest = generate_digest(top, KEYWORDS)

    print("📤 Sending to Telegram...")
    await send_message(digest)
    print("✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())
