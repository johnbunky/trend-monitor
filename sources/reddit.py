"""
Reddit source — uses public RSS feeds, no credentials needed.
Reddit RSS is treated differently from the JSON API and works from cloud IPs.
"""

import httpx
import xml.etree.ElementTree as ET
import asyncio
import time

HEADERS = {"User-Agent": "trend-monitor/1.0 (personal use)"}
SUBREDDITS = ["gamedev", "Unity2D", "love2d", "indiegaming"]

# RSS namespace Reddit uses
NS = {"atom": "http://www.w3.org/2005/Atom"}


async def fetch_reddit(keywords: list[str]) -> list[dict]:
    items = []
    seen = set()

    async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True) as client:
        for subreddit in SUBREDDITS:
            try:
                url = f"https://www.reddit.com/r/{subreddit}/hot.rss?limit=50"
                r = await client.get(url)
                r.raise_for_status()
                posts = _parse_rss(r.text, subreddit)

                for post in posts:
                    if post["id"] not in seen:
                        if _matches(post, keywords):
                            seen.add(post["id"])
                            items.append(post)

                await asyncio.sleep(1)  # be polite

            except Exception as e:
                print(f"  reddit/r/{subreddit} error: {e}")

    return items


def _parse_rss(xml_text: str, subreddit: str) -> list[dict]:
    items = []
    try:
        root = ET.fromstring(xml_text)
        entries = root.findall("atom:entry", NS)

        for entry in entries:
            link = entry.find("atom:link", NS)
            url = link.attrib.get("href", "") if link is not None else ""
            title = entry.findtext("atom:title", "", NS).strip()
            content = entry.findtext("atom:content", "", NS)
            updated = entry.findtext("atom:updated", "", NS)

            # Parse timestamp
            ts = 0
            if updated:
                try:
                    from datetime import datetime, timezone
                    ts = int(datetime.fromisoformat(updated.replace("Z", "+00:00")).timestamp())
                except Exception:
                    pass

            # Strip HTML from content
            import re
            desc = re.sub(r'<[^>]+>', '', content or "")[:300].strip()

            entry_id = url.rstrip("/").split("/")[-2] if url else str(hash(title))

            items.append({
                "id": f"reddit_{entry_id}",
                "source": f"Reddit r/{subreddit}",
                "title": title,
                "url": url,
                "description": desc,
                "score_raw": 0.0,
                "interactions": 0,
                "created_ts": ts,
                "extra": {"subreddit": subreddit},
            })
    except Exception as e:
        print(f"  reddit RSS parse error: {e}")

    return items


def _matches(post: dict, keywords: list[str]) -> bool:
    text = (post["title"] + " " + post["description"]).lower()
    return any(kw.lower() in text for kw in keywords)
