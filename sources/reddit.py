"""
Reddit source — uses public .json API, no credentials needed.
Same data as OAuth, just without voting — which we don't need.
"""

import httpx
import asyncio

HEADERS = {"User-Agent": "trend-monitor/1.0 (personal use)"}
SUBREDDITS = ["gamedev", "Unity2D", "love2d", "indiegaming"]


async def fetch_reddit(keywords: list[str]) -> list[dict]:
    items = []

    async with httpx.AsyncClient(headers=HEADERS, timeout=10) as client:
        for subreddit in SUBREDDITS:
            try:
                url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=50"
                r = await client.get(url)
                r.raise_for_status()
                posts = r.json()["data"]["children"]

                for child in posts:
                    post = child["data"]
                    if _matches(post, keywords):
                        items.append(_normalise(post, subreddit))

                await asyncio.sleep(1)  # be polite between subreddits

            except Exception as e:
                print(f"  reddit/r/{subreddit} error: {e}")

    return items


def _matches(post: dict, keywords: list[str]) -> bool:
    text = (post.get("title", "") + " " + post.get("selftext", "")[:500]).lower()
    return any(kw.lower() in text for kw in keywords)


def _normalise(post: dict, subreddit: str) -> dict:
    return {
        "id": f"reddit_{post.get('id', '')}",
        "source": f"Reddit r/{subreddit}",
        "title": post.get("title", ""),
        "url": f"https://reddit.com{post.get('permalink', '')}",
        "description": post.get("selftext", "")[:300].strip(),
        "score_raw": float(post.get("score", 0)),
        "interactions": int(post.get("num_comments", 0)),
        "created_ts": int(post.get("created_utc", 0)),
        "extra": {
            "upvote_ratio": post.get("upvote_ratio", 0),
            "flair": post.get("link_flair_text", ""),
            "author": post.get("author", ""),
        },
    }
