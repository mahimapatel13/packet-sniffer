from fastapi import APIRouter, HTTPException, status
from typing import List
from application.dtos import CaptureStartRequest, InterfaceDTO
from application.services import global_coordinator
from core.logging import logger

router = APIRouter(prefix="/capture", tags=["Capture Control"])

@router.get("/interfaces", response_model=List[InterfaceDTO])
async def get_interfaces():
    """
    Returns available dynamic network interfaces detected on the host system.
    Compatible with Windows (Npcap) and Linux (libpcap/raw sockets).
    """
    try:
        ifaces = await global_coordinator.list_interfaces()
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
