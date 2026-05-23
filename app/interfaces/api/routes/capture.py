from fastapi import APIRouter, HTTPException, status
from typing import List
from app.application.dtos import CaptureStartRequest, InterfaceDTO
from app.application.services import global_coordinator
from app.core.logging import logger

router = APIRouter(prefix="/capture", tags=["Capture Control"])
@router.get("/interfaces", response_model=List[InterfaceDTO])
async def get_interfaces():
    try:
        ifaces = global_coordinator.list_interfaces()
        return [
            InterfaceDTO(
                name=i.name,
                description=i.description,
                ip_addresses=i.ip_addresses,
                mac_address=i.mac_address,
                is_loopback=i.is_loopback,
                is_up=i.is_up
            )
            for i in ifaces
        ]
    except Exception as e:
        logger.error(f"Error fetching interfaces: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query network interfaces: {str(e)}"
        )
        
@router.get("/interfaces/debug")
async def debug_interfaces():
    import psutil
    from scapy.all import conf
    
    scapy_ifaces = []
    try:
        for k, v in conf.ifaces.items():
            scapy_ifaces.append({
                "key": str(k),
                "name": getattr(v, "name", None),
                "ip": str(getattr(v, "ip", None)),
                "mac": getattr(v, "mac", None),
            })
    except Exception as e:
        scapy_ifaces = [{"error": str(e)}]

    psutil_ifaces = []
    try:
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        for name, addr_list in addrs.items():
            psutil_ifaces.append({
                "name": name,
                "is_up": stats[name].isup if name in stats else None,
                "addrs": [{"family": str(a.family), "address": a.address} for a in addr_list]
            })
    except Exception as e:
        psutil_ifaces = [{"error": str(e)}]

    return {"scapy": scapy_ifaces, "psutil": psutil_ifaces}

    try:
        ifaces = global_coordinator.list_interfaces()
        return [
            InterfaceDTO(
                name=i.name,
                description=i.description,
                ip_addresses=i.ip_addresses,
                mac_address=i.mac_address,
                is_loopback=i.is_loopback,
                is_up=i.is_up
            )
            for i in ifaces
        ]
    except Exception as e:
        logger.error(f"Error fetching interfaces: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query network interfaces: {str(e)}"
        )
@router.post("/start", status_code=status.HTTP_200_OK)
async def start_capture(payload: CaptureStartRequest):
    """
    Initiates dynamic packet capture on the specified interface.
    Resets real-time statistics engines.
    """
    try:
        res = await global_coordinator.start_capture(payload.interface)
        return res
    except Exception as e:
        logger.error(f"Failed to start packet capture session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sniffing initialization failure: {str(e)}"
        )

@router.post("/stop", status_code=status.HTTP_200_OK)
async def stop_capture():
    """
    Terminates active packet capturing sessions on all interfaces.
    Persists finalized session metadata to database.
    """
    try:
        res = await global_coordinator.stop_capture()
        return res
    except Exception as e:
        logger.error(f"Failed to terminate capture session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop active capture engines: {str(e)}"
        )
