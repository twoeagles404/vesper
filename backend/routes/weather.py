import httpx
from fastapi import APIRouter
from backend.config import settings

router = APIRouter()

ICON_URL = "https://openweathermap.org/img/wn/{}@2x.png"


@router.get("/weather")
async def get_weather():
    if not settings.openweather_api_key:
        return {"status": "unconfigured", "message": "Set OPENWEATHER_API_KEY in .env"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "q": settings.weather_city,
                    "appid": settings.openweather_api_key,
                    "units": settings.weather_units,
                },
            )
            resp.raise_for_status()
            d = resp.json()

        unit = "°C" if settings.weather_units == "metric" else "°F"
        return {
            "status": "ok",
            "city": d["name"],
            "temp": round(d["main"]["temp"]),
            "feels_like": round(d["main"]["feels_like"]),
            "humidity": d["main"]["humidity"],
            "description": d["weather"][0]["description"].title(),
            "icon": d["weather"][0]["icon"],
            "icon_url": ICON_URL.format(d["weather"][0]["icon"]),
            "unit": unit,
            "wind_speed": round(d["wind"]["speed"]),
        }
    except httpx.HTTPStatusError as e:
        return {"status": "error", "message": f"API error {e.response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
