import asyncio
import feedparser
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter
from backend.config import settings

router = APIRouter()
_executor = ThreadPoolExecutor(max_workers=4)


def _parse_feed(url: str) -> list:
    try:
        feed = feedparser.parse(url)
        source_name = feed.feed.get("title", url.split("/")[2])
        articles = []
        for entry in feed.entries[:5]:
            articles.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", "#"),
                "source": source_name,
                "published": entry.get("published", ""),
            })
        return articles
    except Exception:
        return []


@router.get("/feeds")
async def get_feeds():
    if not settings.rss_feeds:
        return {"status": "unconfigured", "articles": []}

    urls = [u.strip() for u in settings.rss_feeds.split(",") if u.strip()]
    loop = asyncio.get_event_loop()

    results = await asyncio.gather(
        *[loop.run_in_executor(_executor, _parse_feed, url) for url in urls]
    )

    # Interleave articles from each feed instead of dumping one at a time
    articles = []
    max_len = max((len(r) for r in results), default=0)
    for i in range(max_len):
        for result in results:
            if i < len(result):
                articles.append(result[i])

    return {"status": "ok", "articles": articles[:15]}
