import asyncio
import feedparser
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter
from backend import config_store

router = APIRouter()
_executor = ThreadPoolExecutor(max_workers=4)


def _parse(url: str) -> list:
    try:
        feed = feedparser.parse(url)
        name = feed.feed.get("title", url.split("/")[2])
        return [{"title": e.get("title",""), "link": e.get("link","#"), "source": name} for e in feed.entries[:5]]
    except Exception:
        return []


@router.get("/feeds")
async def get_feeds():
    cfg = config_store.load()["feeds"]
    raw = cfg.get("urls", "")
    if not raw.strip():
        return {"status": "unconfigured", "articles": []}
    urls = [u.strip() for u in raw.split(",") if u.strip()]
    loop = asyncio.get_event_loop()
    results = await asyncio.gather(*[loop.run_in_executor(_executor, _parse, u) for u in urls])
    articles = []
    max_len = max((len(r) for r in results), default=0)
    for i in range(max_len):
        for r in results:
            if i < len(r):
                articles.append(r[i])
    return {"status": "ok", "articles": articles[:15]}
