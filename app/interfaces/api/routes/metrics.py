from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Dict, Any
from app.application.dtos import StatsSummaryDTO, AlertDTO, ProtocolStatItem, TopIPItem, TopDomainItem, GeoPointDTO
from app.application.services import global_coordinator
from app.infrastructure.services.stats import global_stats_engine
from app.core.logging import logger

router = APIRouter(tags=["Metrics & Analysis"])

@router.get("/statistics", response_model=StatsSummaryDTO)
async def get_statistics():
    """
    Returns real-time aggregated traffic statistics, including packet counts,
    active data rate (bytes/sec), packets/sec, and active connection tracking.
    """
    try:
        stats = global_stats_engine.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching stats summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stats calculation error: {str(e)}"
        )

@router.get("/alerts", response_model=List[AlertDTO])
async def get_alerts(limit: int = Query(default=100, ge=1, le=500)):
    """
    Returns historical threat detection logs triggered by the IDS engine.
    """
    try:
        alerts = await global_coordinator.get_alerts_history(limit)
        return [
            AlertDTO(
                id=a.id,
                timestamp=a.timestamp,
                severity=a.severity,
                message=a.message,
                source_ip=a.source_ip
            )
            for a in alerts
        ]
    except Exception as e:
        logger.error(f"Error reading security alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query database alerts: {str(e)}"
        )

@router.get("/protocols", response_model=Dict[str, ProtocolStatItem])
async def get_protocols():
    """
    Returns distribution counts and percentage values per identified protocol layer.
    """
    try:
        dist = global_stats_engine.get_protocol_distribution()
        return {
            proto: ProtocolStatItem(count=item["count"], percentage=item["percentage"])
            for proto, item in dist.items()
        }
    except Exception as e:
        logger.error(f"Error generating protocol distribution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Protocol breakdown calculation failed: {str(e)}"
        )

@router.get("/top-ips")
async def get_top_ips(limit: int = Query(default=5, ge=1, le=50)):
    """
    Returns the most active Source and Destination IP addresses.
    """
    try:
        data = global_stats_engine.get_top_ips(limit)
        return {
            "sources": [TopIPItem(ip=item["ip"], count=item["count"]) for item in data["sources"]],
            "destinations": [TopIPItem(ip=item["ip"], count=item["count"]) for item in data["destinations"]]
        }
    except Exception as e:
        logger.error(f"Error compiling top IPs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve top traffic sources: {str(e)}"
        )

@router.get("/top-domains", response_model=List[TopDomainItem])
async def get_top_domains(limit: int = Query(default=5, ge=1, le=50)):
    """
    Returns the most frequently requested destination domains, resolved dynamically.
    """
    try:
        data = global_stats_engine.get_top_domains(limit)
        return [TopDomainItem(domain=item["domain"], count=item["count"]) for item in data]
    except Exception as e:
        logger.error(f"Error resolving top domains: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to aggregate top requested domains: {str(e)}"
        )
        
@router.get("/geo-points", response_model=List[GeoPointDTO])
async def get_geo_points(limit: int = Query(default=100, ge=1, le=500)):
    """
    Returns geo-resolved source and destination IPs with coordinates,
    country, city, packet counts, and direction.
    Returns empty list if GeoLite2 database is not installed.
    """
    try:
        data = global_stats_engine.get_geo_points(limit)
        return [GeoPointDTO(**item) for item in data]
    except Exception as e:
        logger.error(f"Error fetching geo points: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch geo points: {str(e)}"
        )
        
@router.get("/graph")
async def get_graph():
    stats = global_stats_engine.get_stats()

    nodes = [
        {
            "id": "host",
            "label": "Host",
            "kind": "host"
        }
    ]

    edges = []

    for src in stats["top_source_ips"]:
        ip = src["ip"]

        nodes.append({
            "id": ip,
            "label": ip,
            "kind": "source"
        })

        edges.append({
            "source": ip,
            "target": "host",
            "weight": src["count"]
        })

    return {
        "nodes": nodes,
        "edges": edges
    }
