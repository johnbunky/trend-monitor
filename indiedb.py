"""
IndieDB source — RSS feed, keyword filtered.
Pure indie signal, no Steam noise.
"""

import httpx
import xml.etree.ElementTree as ET
import time
from email.utils import parsedate_to_datetime

FEEDS = [
    "https://www.indiedb.com/games/feed/",
    "https://www.indiedb.com/news/feed/",
]
LOOKBACK_SECONDS = 86400 * 2  # 48h — RSS updates are slower


async def fetch_indiedb(keywords: list[str]) -> list[dict]:
    cutoff = time.time() - LOOKBACK_SECONDS
    items = []

    async with httpx.AsyncClient(
        timeout=20,
        headers={"User-Agent": "TrendMonitorBot/1.0"},
        follow_redirects=True,
    ) as client:
        for feed_url in FEEDS:
            try:
                r = await client.get(feed_url)
                r.raise_for_status()
                root = ET.fromstring(r.text)
                channel = root.find("channel")
                if channel is None:
                    continue

                for item in channel.findall("item"):
                    entry = _parse_item(item)
                    if not entry:
                        continue
                    if entry["created_ts"] < cutoff:
                        continue
                    if _matches(entry, keywords):
                        items.append(entry)
            except Exception as e:
                print(f"  IndieDB feed error ({feed_url}): {e}")

    # Deduplicate
    seen = set()
    unique = []
    for item in items:
        if item["id"] not in seen:
            seen.add(item["id"])
            unique.append(item)

    return unique


def _parse_item(item: ET.Element) -> dict | None:
    try:
        link = item.findtext("link", "").strip()
        title = item.findtext("title", "").strip()
        desc = item.findtext("description", "").strip()
        pub_date = item.findtext("pubDate", "")

        ts = 0
        if pub_date:
            try:
                ts = parsedate_to_datetime(pub_date).timestamp()
            except Exception:
                pass

        return {
            "id": f"indiedb_{hash(link)}",
            "source": "IndieDB",
            "title": title,
            "url": link,
            "description": desc[:300],
            "score_raw": 0.0,
            "interactions": 0,
            "created_ts": int(ts),
            "extra": {},
        }
    except Exception:
        return None


def _matches(entry: dict, keywords: list[str]) -> bool:
    text = (entry["title"] + " " + entry["description"]).lower()
    return any(kw.lower() in text for kw in keywords)
