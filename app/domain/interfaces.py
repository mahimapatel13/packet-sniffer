from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities import TrafficRecord, Alert, Session

class ITrafficRepository(ABC):
    @abstractmethod
    async def save(self, record: TrafficRecord) -> TrafficRecord:
        pass

    @abstractmethod
    async def save_batch(self, records: List[TrafficRecord]) -> None:
        pass

    @abstractmethod
    async def get_history(self, page: int, limit: int) -> List[TrafficRecord]:
        pass

    @abstractmethod
    async def get_total_count(self) -> int:
        pass

class IAlertRepository(ABC):
    @abstractmethod
    async def save(self, alert: Alert) -> Alert:
        pass

    @abstractmethod
    async def get_all(self, limit: int = 100) -> List[Alert]:
        pass

class ISessionRepository(ABC):
    @abstractmethod
    async def create(self, session: Session) -> Session:
        pass

    @abstractmethod
    async def update(self, session: Session) -> Session:
        pass

    @abstractmethod
    async def get_active(self) -> Optional[Session]:
        pass

    @abstractmethod
    async def get_by_id(self, session_id: int) -> Optional[Session]:
        pass
