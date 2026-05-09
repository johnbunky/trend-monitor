"""
GameFromScratch + Game Developer RSS — replaces IndieDB (403).
Both are bot-friendly and indie game dev focused.
"""

import httpx
import xml.etree.ElementTree as ET
import re
import time
from email.utils import parsedate_to_datetime

FEEDS = [
    "https://gamefromscratch.com/feed/",
    "https://www.gamedeveloper.com/rss.xml",
]
LOOKBACK_SECONDS = 86400 * 2

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; TrendMonitorBot/1.0)",
}


async def fetch_indiedb(keywords: list[str]) -> list[dict]:
    cutoff = time.time() - LOOKBACK_SECONDS
    items = []

    async with httpx.AsyncClient(timeout=20, headers=HEADERS, follow_redirects=True) as client:
        for feed_url in FEEDS:
            try:
                r = await client.get(feed_url)
                r.raise_for_status()
                root = ET.fromstring(r.text)
                channel = root.find("channel")
                if channel is None:
                    continue
                for item in channel.findall("item"):
                    entry = _parse_item(item, feed_url)
                    if not entry:
                        continue
                    if entry["created_ts"] > 0 and entry["created_ts"] < cutoff:
                        continue
                    if _matches(entry, keywords):
                        items.append(entry)
            except Exception as e:
                print(f"  RSS feed error ({feed_url}): {e}")

    seen = set()
    unique = []
    for item in items:
        if item["id"] not in seen:
            seen.add(item["id"])
            unique.append(item)

    return unique


def _parse_item(item: ET.Element, feed_url: str) -> dict | None:
    try:
        link = item.findtext("link", "").strip()
        title = item.findtext("title", "").strip()
        desc = re.sub(r'<[^>]+>', '', item.findtext("description", ""))[:300]
        pub_date = item.findtext("pubDate", "")
        ts = 0
        if pub_date:
            try:
                ts = parsedate_to_datetime(pub_date).timestamp()
            except Exception:
                pass
        source_name = "GameFromScratch" if "gamefromscratch" in feed_url else "Game Developer"
        return {
            "id": f"gfs_{hash(link)}",
            "source": source_name,
            "title": title,
            "url": link,
            "description": desc,
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
