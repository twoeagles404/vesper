import httpx
from fastapi import APIRouter
from backend import config_store

router = APIRouter()
GMAIL_API = "https://gmail.googleapis.com/gmail/v1/users/me"


async def _refresh_token(client, cfg):
    if not all([cfg.get("client_id"), cfg.get("client_secret"), cfg.get("refresh_token")]):
        return None
    resp = await client.post("https://oauth2.googleapis.com/token", data={
        "grant_type": "refresh_token",
        "refresh_token": cfg["refresh_token"],
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
    })
    return resp.json().get("access_token") if resp.status_code == 200 else None


def _header(headers, name):
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


@router.get("/email")
async def get_email():
    cfg = config_store.load()["gmail"]
    if not cfg.get("client_id"):
        return {"status": "unconfigured", "messages": []}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            token = await _refresh_token(client, cfg)
            if not token:
                return {"status": "error", "message": "Token refresh failed — check Gmail credentials in Settings"}
            hdrs = {"Authorization": f"Bearer {token}"}
            r = await client.get(f"{GMAIL_API}/messages", headers=hdrs,
                                 params={"labelIds": "INBOX", "maxResults": 10})
            r.raise_for_status()
            msgs = []
            for m in r.json().get("messages", []):
                mr = await client.get(f"{GMAIL_API}/messages/{m['id']}", headers=hdrs,
                                      params={"format": "metadata",
                                              "metadataHeaders": ["From", "Subject", "Date"]})
                if mr.status_code != 200:
                    continue
                data = mr.json()
                h = data.get("payload", {}).get("headers", [])
                from_raw = _header(h, "From")
                from_clean = from_raw.split("<")[0].strip().strip('"') if "<" in from_raw else from_raw
                msgs.append({
                    "from": from_clean,
                    "subject": _header(h, "Subject") or "(no subject)",
                    "date": _header(h, "Date")[:16],
                    "unread": "UNREAD" in data.get("labelIds", []),
                })
        return {"status": "ok", "messages": msgs}
    except Exception as e:
        return {"status": "error", "message": str(e)}
