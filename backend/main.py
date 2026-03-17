import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import proxmox, weather, calendar, feeds, health, email

app = FastAPI(title="Vesper Dashboard", version="1.0.0")

# CORS — open for local network access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# API routes
app.include_router(proxmox.router, prefix="/api")
app.include_router(weather.router, prefix="/api")
app.include_router(calendar.router, prefix="/api")
app.include_router(feeds.router, prefix="/api")
app.include_router(health.router, prefix="/api")
app.include_router(email.router, prefix="/api")

# Resolve frontend path relative to this file (works both locally and in Docker)
FRONTEND_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "frontend"
)


@app.get("/ping")
async def ping():
    """Health check endpoint for Docker."""
    return {"status": "ok", "service": "vesper"}


@app.get("/")
async def root():
    return FileResponse(os.path.join(FRONTEND_PATH, "index.html"))


# Serve static assets (CSS, JS, images if any are added later)
if os.path.isdir(FRONTEND_PATH):
    app.mount("/", StaticFiles(directory=FRONTEND_PATH, html=True), name="frontend")
