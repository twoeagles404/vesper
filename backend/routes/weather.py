import httpx
from fastapi import APIRouter
from backend import config_store

router = APIRouter()


@router.get("/weather")
async def get_weather():
    cfg = config_store.load()["weather"]
    if not cfg.get("api_key"):
        return {"status": "unconfigured"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"q": cfg["city"], "appid": cfg["api_key"], "units": cfg["units"]},
            )
            resp.raise_for_status()
            d = resp.json()
        unit = "°C" if cfg["units"] == "metric" else "°F"
        return {
            "status": "ok",
            "city": d["name"],
            "temp": round(d["main"]["temp"]),
            "feels_like": round(d["main"]["feels_like"]),
            "humidity": d["main"]["humidity"],
            "description": d["weather"][0]["description"].title(),
            "icon": d["weather"][0]["icon"],
            "icon_url": f"https://openweathermap.org/img/wn/{d['weather'][0]['icon']}@2x.png",
            "unit": unit,
            "wind_speed": round(d["wind"]["speed"]),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
