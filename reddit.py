"""
Reddit source — r/Unity2D and r/love2d, last 24h posts.
Uses the official Reddit OAuth2 API (read-only app).
"""

import httpx
import os
import time
from datetime import datetime, timezone, timedelta

SUBREDDITS = ["Unity2D", "love2d", "gamedev", "indiegaming"]
REDDIT_TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
REDDIT_API_URL = "https://oauth.reddit.com"
USER_AGENT = "TrendMonitorBot/1.0 (by /u/trendmonitorbot)"
LOOKBACK_SECONDS = 86400  # 24h


async def _get_token(client: httpx.AsyncClient) -> str:
    client_id = os.environ["REDDIT_CLIENT_ID"]
    client_secret = os.environ["REDDIT_CLIENT_SECRET"]
    r = await client.post(
        REDDIT_TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(client_id, client_secret),
        headers={"User-Agent": USER_AGENT},
    )
    r.raise_for_status()
    return r.json()["access_token"]


async def fetch_reddit(keywords: list[str]) -> list[dict]:
    cutoff = time.time() - LOOKBACK_SECONDS
    items = []

    async with httpx.AsyncClient(timeout=15) as client:
        token = await _get_token(client)
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": USER_AGENT,
        }

        for sub in SUBREDDITS:
            try:
                r = await client.get(
                    f"{REDDIT_API_URL}/r/{sub}/new.json",
                    headers=headers,
                    params={"limit": 100},
                )
                r.raise_for_status()
                posts = r.json()["data"]["children"]

                for post in posts:
                    p = post["data"]
                    if p["created_utc"] < cutoff:
                        continue
                    if _matches(p, keywords):
                        items.append(_normalise(p, sub))
            except Exception as e:
                print(f"  reddit/{sub} error: {e}")

    return items


def _matches(post: dict, keywords: list[str]) -> bool:
    text = " ".join([
        post.get("title", ""),
        post.get("selftext", "")[:500],
        post.get("link_flair_text", "") or "",
    ]).lower()
    return any(kw.lower() in text for kw in keywords)


def _normalise(post: dict, subreddit: str) -> dict:
    return {
        "id": f"reddit_{post['id']}",
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
