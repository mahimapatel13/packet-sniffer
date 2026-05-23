import threading
from typing import Optional, Dict
from pathlib import Path
from pydantic import BaseModel
from app.core.config import settings
from app.core.logging import logger
import geoip2.database


class GeoLocation(BaseModel):
    ip: str
    country_code: str
    country_name: str
    city: Optional[str] = None
    latitude: float
    longitude: float


PRIVATE_PREFIXES = (
    "10.", "192.168.", "127.", "0.", "169.254.",
    "172.16.", "172.17.", "172.18.", "172.19.",
    "172.20.", "172.21.", "172.22.", "172.23.",
    "172.24.", "172.25.", "172.26.", "172.27.",
    "172.28.", "172.29.", "172.30.", "172.31.",
    "::1", "fc", "fd",
)


def is_private(ip: str) -> bool:
    return any(ip.startswith(prefix) for prefix in PRIVATE_PREFIXES)


class GeoResolver:
    """
    Thread-safe singleton that resolves IPs to geo coordinates
    using the offline MaxMind GeoLite2-City database.
    Results are cached indefinitely in memory — geo data
    does not change for a given IP within a session.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._cache: Dict[str, Optional[GeoLocation]] = {}
        self._reader = None
        self._available = False
        self._load_database()

    def _load_database(self) -> None:
        db_path = Path(settings.GEOIP_DB_PATH)
        if not db_path.exists():
            logger.warning(
                f"GeoLite2 database not found at {db_path}. "
                f"Geo-IP resolution disabled. "
                f"Download from https://dev.maxmind.com/geoip/geolite2-free-geolocation-data"
            )
            return
        try:
            self._reader = geoip2.database.Reader(str(db_path))
            self._available = True
            logger.info(f"GeoLite2 database loaded from {db_path}")
        except Exception as e:
            logger.error(f"Failed to load GeoLite2 database: {e}")

    def resolve(self, ip: str) -> Optional[GeoLocation]:
        """
        Returns GeoLocation for a given IP, or None if:
        - IP is private/reserved
        - database not loaded
        - IP not found in database
        - any exception occurs
        Result is cached so each IP is only looked up once per session.
        Thread-safe — called from Scapy capture threads.
        """
        if not self._available or not ip:
            return None

        if is_private(ip):
            return None

        with self._lock:
            if ip in self._cache:
                return self._cache[ip]

        result = self._lookup(ip)

        with self._lock:
            self._cache[ip] = result

        return result

    def _lookup(self, ip: str) -> Optional[GeoLocation]:
        try:
            response = self._reader.city(ip)
            return GeoLocation(
                ip=ip,
                country_code=response.country.iso_code or "XX",
                country_name=response.country.name or "Unknown",
                city=response.city.name,
                latitude=float(response.location.latitude or 0.0),
                longitude=float(response.location.longitude or 0.0),
            )
        except Exception:
            return None

    def cache_size(self) -> int:
        with self._lock:
            return len(self._cache)

    def is_available(self) -> bool:
        return self._available

    def shutdown(self) -> None:
        if self._reader:
            try:
                self._reader.close()
            except Exception:
                pass


geo_resolver = GeoResolver()