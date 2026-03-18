import asyncio
import httpx
from fastapi import APIRouter
from backend import config_store

router = APIRouter()


async def _check(name: str, url: str) -> dict:
    try:
        async with httpx.AsyncClient(verify=False, timeout=5) as client:
            resp = await client.get(url, follow_redirects=True)
            return {"name": name, "url": url, "status": "up", "code": resp.status_code,
                    "response_ms": int(resp.elapsed.total_seconds() * 1000)}
    except httpx.TimeoutException:
        return {"name": name, "url": url, "status": "down", "reason": "timeout"}
    except Exception as e:
        return {"name": name, "url": url, "status": "down", "reason": str(e)[:60]}


@router.get("/health")
async def get_health():
    cfg = config_store.load()["services"]
    raw = cfg.get("list", "")
    if not raw.strip():
        return {"status": "unconfigured", "services": []}
    pairs = []
    for item in raw.split(","):
        item = item.strip()
        if "=" in item:
            name, url = item.split("=", 1)
            pairs.append((name.strip(), url.strip()))
    if not pairs:
        return {"status": "ok", "services": []}
    results = await asyncio.gather(*[_check(n, u) for n, u in pairs])
    return {"status": "ok", "services": list(results)}
