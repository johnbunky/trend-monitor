import httpx, xml.etree.ElementTree as ET, re, time
from email.utils import parsedate_to_datetime

FEEDS = ["https://gamefromscratch.com/feed/", "https://www.gamedeveloper.com/rss.xml"]
LOOKBACK_SECONDS = 86400 * 2
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TrendMonitorBot/1.0)"}

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
                if channel is None: continue
                for item in channel.findall("item"):
                    link = item.findtext("link", "").strip()
                    title = item.findtext("title", "").strip()
                    desc = re.sub(r'<[^>]+>', '', item.findtext("description", ""))[:300]
                    pub_date = item.findtext("pubDate", "")
                    ts = 0
                    if pub_date:
                        try: ts = parsedate_to_datetime(pub_date).timestamp()
                        except: pass
                    if ts > 0 and ts < cutoff: continue
                    source = "GameFromScratch" if "gamefromscratch" in feed_url else "Game Developer"
                    items.append({
                        "id": f"gfs_{hash(link)}", "source": source,
                        "title": title, "url": link, "description": desc,
                        "score_raw": 0.0, "interactions": 0, "created_ts": int(ts), "extra": {},
                    })
            except Exception as e:
                print(f"  RSS error ({feed_url}): {e}")
    return items
