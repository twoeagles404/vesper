import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter
from proxmoxer import ProxmoxAPI
from backend import config_store

router = APIRouter()
_executor = ThreadPoolExecutor(max_workers=4)


def _get_client():
    cfg = config_store.load()["proxmox"]
    return ProxmoxAPI(
        cfg["host"],
        port=int(cfg["port"]),
        user=cfg["user"],
        password=cfg["password"],
        verify_ssl=cfg["verify_ssl"],
    )


def _fetch_node_status():
    cfg = config_store.load()["proxmox"]
    if not cfg.get("host") or not cfg.get("password"):
        return {"status": "unconfigured"}
    try:
        px = _get_client()
        node = cfg["node"]
        s = px.nodes(node).status.get()
        return {
            "status": "ok",
            "cpu": round(s["cpu"] * 100, 1),
            "memory": {
                "used": s["memory"]["used"],
                "total": s["memory"]["total"],
                "percent": round(s["memory"]["used"] / s["memory"]["total"] * 100, 1),
            },
            "disk": {
                "used": s["rootfs"]["used"],
                "total": s["rootfs"]["total"],
                "percent": round(s["rootfs"]["used"] / s["rootfs"]["total"] * 100, 1),
            },
            "uptime": s["uptime"],
            "netin":  s.get("netin", 0),
            "netout": s.get("netout", 0),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _fetch_vms():
    cfg = config_store.load()["proxmox"]
    if not cfg.get("host") or not cfg.get("password"):
        return {"status": "unconfigured", "vms": []}
    try:
        px = _get_client()
        node = cfg["node"]
        vms = []
        for vm in px.nodes(node).qemu.get():
            vms.append({
                "id": vm["vmid"], "name": vm.get("name", f"vm-{vm['vmid']}"),
                "type": "vm", "status": vm["status"],
                "cpu": round(vm.get("cpu", 0) * 100, 1),
                "mem": vm.get("mem", 0), "maxmem": vm.get("maxmem", 0),
            })
        for ct in px.nodes(node).lxc.get():
            vms.append({
                "id": ct["vmid"], "name": ct.get("name", f"ct-{ct['vmid']}"),
                "type": "lxc", "status": ct["status"],
                "cpu": round(ct.get("cpu", 0) * 100, 1),
                "mem": ct.get("mem", 0), "maxmem": ct.get("maxmem", 0),
            })
        vms.sort(key=lambda x: x["id"])
        return {"status": "ok", "vms": vms}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/proxmox/node")
async def get_node_status():
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _fetch_node_status)


@router.get("/proxmox/vms")
async def get_vms():
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _fetch_vms)
