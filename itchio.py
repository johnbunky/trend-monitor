"""
Itch.io source — top rated games, keyword filtered.
Uses the public browse API (no auth required).
"""

import httpx
import time
from datetime import datetime, timezone, timedelta

ITCHIO_URL = "https://itch.io/games.json"
LOOKBACK_HOURS = 48  # itch doesn't expose created_at reliably, so we use a wider window


async def fetch_itchio(keywords: list[str]) -> list[dict]:
    params = {
        "classification": "game",
        "sort": "new",
        "limit": 100,
    }

    items = []
    async with httpx.AsyncClient(timeout=15) as client:
        # Fetch new + top-rated pages
        for sort in ("new", "top-rated"):
            params["sort"] = sort
            try:
                r = await client.get(ITCHIO_URL, params=params)
                r.raise_for_status()
                data = r.json()
                games = data.get("games", [])
                for game in games:
                    if _matches(game, keywords):
                        items.append(_normalise(game, sort))
            except Exception:
                pass

    # Deduplicate by id
    seen = set()
    unique = []
    for item in items:
        if item["id"] not in seen:
            seen.add(item["id"])
            unique.append(item)

    return unique


def _matches(game: dict, keywords: list[str]) -> bool:
    text = " ".join([
        game.get("title", ""),
        game.get("short_text", ""),
        " ".join(game.get("tags", []) if isinstance(game.get("tags"), list) else []),
    ]).lower()
    return any(kw.lower() in text for kw in keywords)


def _normalise(game: dict, sort_hint: str) -> dict:
    return {
        "id": f"itchio_{game.get('id')}",
        "source": "Itch.io",
        "title": game.get("title", "Unknown"),
        "url": game.get("url", ""),
        "description": game.get("short_text", ""),
        "score_raw": float(game.get("rating", 0) or 0),
        "interactions": int(game.get("views_count", 0) or 0),
        "created_ts": 0,  # itch API doesn't expose this cleanly
        "extra": {
            "sort": sort_hint,
            "platforms": game.get("platforms", {}),
            "user": game.get("user", {}).get("username", ""),
        },
    }
