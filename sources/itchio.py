import httpx
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

KEYWORD_TAGS = ["game-jam", "atmospheric", "minimalist", "indie", "co-op", "pixel-art", "physics"]

async def fetch_itchio(keywords: list[str]) -> list[dict]:
    items = []
    seen = set()
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        for tag in KEYWORD_TAGS:
            try:
                r = await client.get(f"https://itch.io/games/tag-{tag}.xml")
                r.raise_for_status()
                root = ET.fromstring(r.text)
                for item in root.findall("./channel/item")[:8]:
                    link = item.findtext("link", "").strip()
                    if link in seen: continue
                    seen.add(link)
                    items.append({
                        "id": f"itchio_{hash(link)}",
                        "source": "Itch.io",
                        "title": item.findtext("title", "").strip(),
                        "url": link,
                        "description": item.findtext("description", "")[:200],
                        "score_raw": 0.0, "interactions": 0, "created_ts": 0,
                        "extra": {"tag": tag},
                    })
            except Exception as e:
                print(f"  itch/{tag} error: {e}")
    return items
