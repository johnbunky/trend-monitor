"""
Hacker News source — via Algolia API, last 24h.
No auth required. Great for "game feel" breakthroughs.
"""

import httpx
import time

ALGOLIA_URL = "https://hn.algolia.com/api/v1/search_by_date"
LOOKBACK_SECONDS = 86400


async def fetch_hackernews(keywords: list[str]) -> list[dict]:
    cutoff = int(time.time() - LOOKBACK_SECONDS)
    items = []
    seen = set()

    async with httpx.AsyncClient(timeout=15) as client:
        for kw in keywords:
            try:
                r = await client.get(
                    ALGOLIA_URL,
                    params={
                        "query": kw,
                        "tags": "(story,show_hn)",
                        "numericFilters": f"created_at_i>{cutoff}",
                        "hitsPerPage": 20,
                    },
                )
                r.raise_for_status()
                hits = r.json().get("hits", [])

                for hit in hits:
                    obj_id = hit.get("objectID")
                    if obj_id in seen:
                        continue
                    seen.add(obj_id)
                    items.append(_normalise(hit))
            except Exception as e:
                print(f"  HN/{kw} error: {e}")

    return items


def _normalise(hit: dict) -> dict:
    story_id = hit.get("objectID", "")
    return {
        "id": f"hn_{story_id}",
        "source": "Hacker News",
        "title": hit.get("title", ""),
        "url": hit.get("url") or f"https://news.ycombinator.com/item?id={story_id}",
        "description": hit.get("story_text", "") or "",
        "score_raw": float(hit.get("points", 0) or 0),
        "interactions": int(hit.get("num_comments", 0) or 0),
        "created_ts": int(hit.get("created_at_i", 0) or 0),
        "extra": {
            "author": hit.get("author", ""),
            "hn_url": f"https://news.ycombinator.com/item?id={story_id}",
        },
    }
