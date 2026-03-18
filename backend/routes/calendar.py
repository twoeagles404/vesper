import httpx
from fastapi import APIRouter
from icalendar import Calendar
from datetime import datetime, date, timezone
from dateutil.relativedelta import relativedelta
from backend import config_store

router = APIRouter()


@router.get("/calendar")
async def get_calendar():
    cfg = config_store.load()["calendar"]
    if not cfg.get("ical_url"):
        return {"status": "unconfigured", "events": []}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(cfg["ical_url"])
            resp.raise_for_status()
        cal = Calendar.from_ical(resp.content)
        now = datetime.now(tz=timezone.utc)
        cutoff = now + relativedelta(weeks=2)
        events = []
        for component in cal.walk():
            if component.name != "VEVENT":
                continue
            dtstart = component.get("dtstart")
            if not dtstart:
                continue
            start = dtstart.dt
            if isinstance(start, date) and not isinstance(start, datetime):
                start = datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
            elif isinstance(start, datetime) and start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            if now <= start <= cutoff:
                events.append({
                    "title": str(component.get("summary", "No Title")),
                    "start": start.isoformat(),
                    "all_day": not hasattr(dtstart.dt, "hour"),
                    "location": str(component.get("location", "")) or None,
                })
        events.sort(key=lambda x: x["start"])
        return {"status": "ok", "events": events[:10]}
    except Exception as e:
        return {"status": "error", "message": str(e)}
