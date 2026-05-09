#!/usr/bin/env python3
import asyncio
import sys
from itchio import fetch_itchio
from redit import fetch_reddit
from hackernews import fetch_hackernews
from indiedb import fetch_indiedb
from scorer import score_items
from digest import generate_digest
from telegrambot import send_message

KEYWORDS = [
    "kinetic satisfaction", "minimalist physics", "emergent storytelling",
    "atmospheric indie", "co-op mechanics", "game feel", "juice", "game jam",
]
TOP_N = 8

async def main():
    print("🔍 Fetching from all sources...")
    results = []
    for fetcher, name in [
        (fetch_itchio, "Itch.io"), (fetch_reddit, "Reddit"),
        (fetch_hackernews, "Hacker News"), (fetch_indiedb, "IndieDB"),
    ]:
        try:
            items = await fetcher(KEYWORDS)
            print(f"  ✅ {name}: {len(items)} items")
            results += items
        except Exception as e:
            print(f"  ⚠️  {name} failed: {e}", file=sys.stderr)

    print(f"\n📦 Total raw items: {len(results)}")
    if not results:
        await send_message("📭 *Trend Monitor* — no items found today.")
        return

    scored = score_items(results)[:TOP_N]
    digest = generate_digest(scored, KEYWORDS)
    await send_message(digest)
    print("✅ Done!")

if __name__ == "__main__":
    asyncio.run(main())
