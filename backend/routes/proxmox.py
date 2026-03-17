import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter
from proxmoxer import ProxmoxAPI
from backend.config import settings

router = APIRouter()
_executor = ThreadPoolExecutor(max_workers=4)


def _get_client():
    return ProxmoxAPI(
        settings.proxmox_host,
        port=settings.proxmox_port,
        user=settings.proxmox_user,
        password=settings.proxmox_password,
        verify_ssl=settings.proxmox_verify_ssl,
    )


def _fetch_node_status():
    try:
        px = _get_client()
        node = settings.proxmox_node
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
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _fetch_vms():
    try:
        px = _get_client()
        node = settings.proxmox_node
        vms = []

        for vm in px.nodes(node).qemu.get():
            vms.append({
                "id": vm["vmid"],
                "name": vm.get("name", f"vm-{vm['vmid']}"),
                "type": "vm",
                "status": vm["status"],
                "cpu": round(vm.get("cpu", 0) * 100, 1),
                "mem": vm.get("mem", 0),
                "maxmem": vm.get("maxmem", 0),
            })

        for ct in px.nodes(node).lxc.get():
            vms.append({
                "id": ct["vmid"],
                "name": ct.get("name", f"ct-{ct['vmid']}"),
                "type": "lxc",
                "status": ct["status"],
                "cpu": round(ct.get("cpu", 0) * 100, 1),
                "mem": ct.get("mem", 0),
                "maxmem": ct.get("maxmem", 0),
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
