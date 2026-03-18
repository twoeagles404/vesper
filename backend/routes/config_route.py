import copy
from fastapi import APIRouter, Body
from backend import config_store

router = APIRouter()

MASK = "••••••••"
SENSITIVE = [
    ("proxmox", "password"),
    ("gmail", "client_secret"),
    ("gmail", "refresh_token"),
    ("weather", "api_key"),
]


def _mask(cfg: dict) -> dict:
    c = copy.deepcopy(cfg)
    for section, key in SENSITIVE:
        if c.get(section, {}).get(key):
            c[section][key] = MASK
    return c


@router.get("/config")
async def get_config():
    return _mask(config_store.load())


@router.post("/config")
async def post_config(body: dict = Body(...)):
    current = config_store.load()
    for section, val in body.items():
        if isinstance(val, dict):
            if section not in current:
                current[section] = {}
            for k, v in val.items():
                if v != MASK:  # never overwrite with the masked placeholder
                    current[section][k] = v
        else:
            if val != MASK:
                current[section] = val
    config_store.save(current)
    return {"status": "ok"}
