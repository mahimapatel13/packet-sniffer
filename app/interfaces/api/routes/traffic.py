from fastapi import APIRouter, Query, HTTPException, status
from application.dtos import PagedTrafficHistory, TrafficRecordDTO
from application.services import global_coordinator
from core.logging import logger
from typing import List

router = APIRouter(prefix="/traffic", tags=["Traffic Log"])

@router.get("/history", response_model=PagedTrafficHistory)
async def get_traffic_history(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=50, ge=1, le=500, description="Records per page")
):
    """
    Returns a paginated list of historically logged network packets.
    Orders records in descending chronological order.
    """
    try:
        data = await global_coordinator.get_traffic_history(page, limit)
        # Map domain records to DTOs
        records_dto = [
            TrafficRecordDTO(
                id=r.id,
                timestamp=r.timestamp,
                source_ip=r.source_ip,
                destination_ip=r.destination_ip,
                source_port=r.source_port,
                destination_port=r.destination_port,
                protocol=r.protocol,
                packet_size=r.packet_size,
                ttl=r.ttl,
                mac_src=r.mac_src,
                mac_dst=r.mac_dst,
                domain=r.domain,
                payload_len=r.payload_len
            )
            for r in data["records"]
        ]
        return PagedTrafficHistory(
            total=data["total"],
            page=data["page"],
            limit=data["limit"],
            records=records_dto
        )
    except Exception as e:
        logger.error(f"Error reading historical traffic: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query failure: {str(e)}"
        )

@router.get("/live", response_model=List[TrafficRecordDTO])
async def get_live_traffic(limit: int = Query(default=50, ge=1, le=200)):
    """
    Returns the most recently captured packet logs stored in the database.
    Useful for populating standard dashboard logs upon initial boot.
    """
    try:
        # Re-use history querying for page=1
        data = await global_coordinator.get_traffic_history(page=1, limit=limit)
        records_dto = [
            TrafficRecordDTO(
                id=r.id,
                timestamp=r.timestamp,
                source_ip=r.source_ip,
                destination_ip=r.destination_ip,
                source_port=r.source_port,
                destination_port=r.destination_port,
                protocol=r.protocol,
                packet_size=r.packet_size,
                ttl=r.ttl,
                mac_src=r.mac_src,
                mac_dst=r.mac_dst,
                domain=r.domain,
                payload_len=r.payload_len
            )
            for r in data["records"]
        ]
        return records_dto
    except Exception as e:
        logger.error(f"Error querying live traffic records: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query failure: {str(e)}"
        )
