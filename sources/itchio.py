"""
Itch.io source — scrapes tag pages for relevant keywords.
The JSON API returns empty results; tag search pages work reliably.
"""

import httpx
import re

KEYWORD_TAGS = [
    "game-jam", "atmospheric", "minimalist",
    "indie", "co-op", "pixel-art", "physics",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; TrendMonitorBot/1.0)",
    "Accept": "text/html",
}


async def fetch_itchio(keywords: list[str]) -> list[dict]:
    items = []
    seen = set()

    async with httpx.AsyncClient(timeout=20, headers=HEADERS, follow_redirects=True) as client:
        for tag_slug in KEYWORD_TAGS:
            try:
                url = f"https://itch.io/games/tag-{tag_slug}?sort=new"
                r = await client.get(url)
                r.raise_for_status()
                games = _parse_games(r.text, tag_slug)
                for game in games:
                    if game["id"] not in seen:
                        seen.add(game["id"])
                        items.append(game)
            except Exception as e:
                print(f"  itch/{tag_slug} error: {e}")

    return items


def _parse_games(html: str, tag: str) -> list[dict]:
    items = []
    urls = re.findall(r'href="(https://[^"]+\.itch\.io/[^"]+)"', html)
    titles = re.findall(r'class="[^"]*game_title[^"]*"[^>]*>\s*([^<]+)\s*<', html)
    descs = re.findall(r'class="[^"]*game_short_text[^"]*"[^>]*>\s*([^<]+)\s*<', html)

    for i, (url, title) in enumerate(zip(urls[:10], titles[:10])):
        slug = url.rstrip("/").split("/")[-1]
        desc = descs[i].strip() if i < len(descs) else ""
        items.append({
            "id": f"itchio_{slug}",
            "source": "Itch.io",
            "title": title.strip(),
            "url": url,
            "description": desc,
            "score_raw": 0.0,
            "interactions": 0,
            "created_ts": 0,
            "extra": {"tag": tag},
        })

    return items
