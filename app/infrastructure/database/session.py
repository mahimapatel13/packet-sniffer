import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from core.config import settings
from core.logging import logger
from infrastructure.database.models import Base

# Cleanly format database URLs for async drivers if standard sync ones are supplied
db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif db_url.startswith("sqlite://"):
    db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://", 1)

# Ensure correct arguments based on driver
connect_args = {}
if "sqlite" in db_url:
    # SQLite requires check_same_thread=False for multiple threads
    connect_args = {"check_same_thread": False}

logger.info(f"Initializing database engine with connection URL format: {db_url.split('@')[-1] if '@' in db_url else db_url}")

engine = create_async_engine(
    db_url,
    echo=False,
    connect_args=connect_args,
    pool_pre_ping=True
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def init_db() -> None:
    """Utility to dynamically create all tables if they do not exist."""
    try:
        async with engine.begin() as conn:
            # Import models to ensure registered on Base
            from infrastructure.database.models import TrafficRecordModel, AlertModel, SessionModel
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schemas initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database schemas: {e}")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Dependency for database session injection."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
