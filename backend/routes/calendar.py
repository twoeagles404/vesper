import httpx
from fastapi import APIRouter
from icalendar import Calendar
from datetime import datetime, date, timezone
from dateutil.relativedelta import relativedelta
from backend.config import settings

router = APIRouter()


@router.get("/calendar")
async def get_calendar():
    if not settings.ical_url:
        return {"status": "unconfigured", "message": "Set ICAL_URL in .env"}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(settings.ical_url)
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

            # Normalise: all-day events are date objects, timed events are datetime
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
        return {"status": "ok", "events": events[:8]}

    except httpx.HTTPStatusError as e:
        return {"status": "error", "message": f"Calendar fetch failed: {e.response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
