from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from domain.entities import TrafficRecord, Alert, Session
from domain.interfaces import ITrafficRepository, IAlertRepository, ISessionRepository
from infrastructure.database.models import TrafficRecordModel, AlertModel, SessionModel

class TrafficRepository(ITrafficRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _map_to_entity(self, m: TrafficRecordModel) -> TrafficRecord:
        return TrafficRecord(
            id=m.id,
            timestamp=m.timestamp,
            source_ip=m.source_ip,
            destination_ip=m.destination_ip,
            source_port=m.source_port,
            destination_port=m.destination_port,
            protocol=m.protocol,
            packet_size=m.packet_size,
            ttl=m.ttl,
            mac_src=m.mac_src,
            mac_dst=m.mac_dst,
            domain=m.domain,
            payload_len=m.payload_len
        )

    async def save(self, record: TrafficRecord) -> TrafficRecord:
        model = TrafficRecordModel(
            timestamp=record.timestamp,
            source_ip=record.source_ip,
            destination_ip=record.destination_ip,
            source_port=record.source_port,
            destination_port=record.destination_port,
            protocol=record.protocol,
            packet_size=record.packet_size,
            ttl=record.ttl,
            mac_src=record.mac_src,
            mac_dst=record.mac_dst,
            domain=record.domain,
            payload_len=record.payload_len
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._map_to_entity(model)

    async def save_batch(self, records: List[TrafficRecord]) -> None:
        if not records:
            return
        models = [
            TrafficRecordModel(
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
            for r in records
        ]
        self.session.add_all(models)
        await self.session.commit()

    async def get_history(self, page: int, limit: int) -> List[TrafficRecord]:
        offset = (page - 1) * limit
        stmt = (
            select(TrafficRecordModel)
            .order_by(desc(TrafficRecordModel.timestamp))
            .offset(offset)
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [self._map_to_entity(m) for m in models]

    async def get_total_count(self) -> int:
        stmt = select(func.count(TrafficRecordModel.id))
        res = await self.session.execute(stmt)
        return res.scalar() or 0


class AlertRepository(IAlertRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _map_to_entity(self, m: AlertModel) -> Alert:
        return Alert(
            id=m.id,
            timestamp=m.timestamp,
            severity=m.severity,
            message=m.message,
            source_ip=m.source_ip
        )

    async def save(self, alert: Alert) -> Alert:
        model = AlertModel(
            timestamp=alert.timestamp,
            severity=alert.severity,
            message=alert.message,
            source_ip=alert.source_ip
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._map_to_entity(model)

    async def get_all(self, limit: int = 100) -> List[Alert]:
        stmt = (
            select(AlertModel)
            .order_by(desc(AlertModel.timestamp))
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [self._map_to_entity(m) for m in models]


class SessionRepository(ISessionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _map_to_entity(self, m: SessionModel) -> Session:
        return Session(
            id=m.id,
            interface=m.interface,
            status=m.status,
            started_at=m.started_at,
            stopped_at=m.stopped_at
        )

    async def create(self, session: Session) -> Session:
        model = SessionModel(
            interface=session.interface,
            status=session.status,
            started_at=session.started_at,
            stopped_at=session.stopped_at
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._map_to_entity(model)

    async def update(self, session: Session) -> Session:
        model = await self.session.get(SessionModel, session.id)
        if model:
            model.status = session.status
            model.stopped_at = session.stopped_at
            await self.session.commit()
            await self.session.refresh(model)
            return self._map_to_entity(model)
        raise ValueError(f"Session with ID {session.id} not found.")

    async def get_active(self) -> Optional[Session]:
        stmt = (
            select(SessionModel)
            .where(SessionModel.status == "active")
            .order_by(desc(SessionModel.started_at))
            .limit(1)
        )
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        return self._map_to_entity(model) if model else None

    async def get_by_id(self, session_id: int) -> Optional[Session]:
        model = await self.session.get(SessionModel, session_id)
        return self._map_to_entity(model) if model else None
