import httpx
import base64
from fastapi import APIRouter
from backend.config import settings

router = APIRouter()

GMAIL_API = "https://gmail.googleapis.com/gmail/v1/users/me"


async def _refresh_access_token(client: httpx.AsyncClient) -> str | None:
    """Use the refresh token to get a fresh access token."""
    if not settings.gmail_refresh_token or not settings.gmail_client_id or not settings.gmail_client_secret:
        return None
    resp = await client.post(
        "https://oauth2.googleapis.com/token",
        data={
            "grant_type":    "refresh_token",
            "refresh_token": settings.gmail_refresh_token,
            "client_id":     settings.gmail_client_id,
            "client_secret": settings.gmail_client_secret,
        },
    )
    if resp.status_code == 200:
        return resp.json().get("access_token")
    return None


def _parse_header(headers: list, name: str) -> str:
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _clean_from(raw: str) -> str:
    """Extract display name or email from a From: header."""
    if "<" in raw:
        return raw.split("<")[0].strip().strip('"')
    return raw.strip()


@router.get("/email")
async def get_email():
    if not settings.gmail_client_id:
        return {"status": "unconfigured", "messages": []}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            token = await _refresh_access_token(client)
            if not token:
                return {"status": "error", "message": "Could not refresh Gmail token — check credentials in .env"}

            headers = {"Authorization": f"Bearer {token}"}

            # Fetch latest 10 messages from inbox
            list_resp = await client.get(
                f"{GMAIL_API}/messages",
                headers=headers,
                params={"labelIds": "INBOX", "maxResults": 10},
            )
            list_resp.raise_for_status()
            msg_ids = [m["id"] for m in list_resp.json().get("messages", [])]

            messages = []
            for mid in msg_ids:
                msg_resp = await client.get(
                    f"{GMAIL_API}/messages/{mid}",
                    headers=headers,
                    params={"format": "metadata", "metadataHeaders": ["From", "Subject", "Date"]},
                )
                if msg_resp.status_code != 200:
                    continue
                msg = msg_resp.json()
                hdrs = msg.get("payload", {}).get("headers", [])
                label_ids = msg.get("labelIds", [])
                messages.append({
                    "id":      mid,
                    "from":    _clean_from(_parse_header(hdrs, "From")),
                    "subject": _parse_header(hdrs, "Subject") or "(no subject)",
                    "date":    _parse_header(hdrs, "Date")[:16],
                    "unread":  "UNREAD" in label_ids,
                })

            return {"status": "ok", "messages": messages}

    except httpx.HTTPStatusError as e:
        return {"status": "error", "message": f"Gmail API error {e.response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
