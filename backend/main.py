import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import proxmox, weather, calendar, feeds, health, email
from backend.routes import config_route

app = FastAPI(title="Vesper Dashboard", version="2.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(proxmox.router,      prefix="/api")
app.include_router(weather.router,      prefix="/api")
app.include_router(calendar.router,     prefix="/api")
app.include_router(feeds.router,        prefix="/api")
app.include_router(health.router,       prefix="/api")
app.include_router(email.router,        prefix="/api")
app.include_router(config_route.router, prefix="/api")

FRONTEND_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "frontend"
)


@app.get("/ping")
async def ping():
    return {"status": "ok"}


@app.get("/")
async def root():
    return FileResponse(os.path.join(FRONTEND_PATH, "index.html"))


if os.path.isdir(FRONTEND_PATH):
    app.mount("/", StaticFiles(directory=FRONTEND_PATH, html=True), name="frontend")
