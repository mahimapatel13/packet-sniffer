import asyncio
from typing import List, Optional
from domain.entities import TrafficRecord
from infrastructure.database.session import async_session_factory
from infrastructure.database.repositories import TrafficRepository
from core.logging import logger
from core.config import settings

class BatchDatabaseWriter:
    """
    High-performance asynchronous writer that accumulates traffic logs in memory
    and performs bulk database inserts. Thread-safe for external background threads.
    """
    def __init__(self, batch_size: int = settings.BATCH_SIZE, timeout_sec: float = settings.BATCH_TIMEOUT_SEC):
        self.batch_size = batch_size
        self.timeout_sec = timeout_sec
        self._queue: Optional[asyncio.Queue] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._task: Optional[asyncio.Task] = None
        self._is_running = False

    def start(self):
        """Starts the background DB writer task. Must be called within the active asyncio event loop."""
        if self._is_running:
            return
        
        self._loop = asyncio.get_running_loop()
        self._queue = asyncio.Queue()
        self._is_running = True
        self._task = asyncio.create_task(self._worker())
        logger.info("Asynchronous batch database writer started.")

    async def stop(self):
        """Flushes the remaining queue contents and stops the background worker."""
        if not self._is_running:
            return
        
        self._is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            
        await self._flush_remaining()
        logger.info("Asynchronous batch database writer stopped.")

    def enqueue(self, record: TrafficRecord):
        """
        Thread-safe method to enqueue packet records from sniffing threads.
        Bridges the OS thread pool to the asyncio event loop queue safely.
        """
        if not self._is_running or self._queue is None or self._loop is None:
            return

        # Use call_soon_threadsafe to push from external threads to the asyncio queue safely
        self._loop.call_soon_threadsafe(self._queue.put_nowait, record)

    async def _worker(self):
        while self._is_running:
            batch = []
            start_time = self._loop.time()
            
            while len(batch) < self.batch_size:
                elapsed = self._loop.time() - start_time
                remaining = self.timeout_sec - elapsed
                
                if remaining <= 0:
                    break
                
                try:
                    # Fetch from queue
                    item = await asyncio.wait_for(self._queue.get(), timeout=max(0.01, remaining))
                    batch.append(item)
                    self._queue.task_done()
                except asyncio.TimeoutError:
                    break
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.error(f"Error reading from batch queue: {e}")
                    break

            if batch:
                await self._write_batch(batch)

    async def _write_batch(self, batch: List[TrafficRecord]):
        for attempt in range(3):
            try:
                async with async_session_factory() as session:
                    repo = TrafficRepository(session)
                    await repo.save_batch(batch)
                return
            except Exception as e:
                logger.error(f"Failed to bulk save {len(batch)} traffic records (attempt {attempt+1}/3): {e}")
                if attempt < 2:
                    await asyncio.sleep(0.5 * (attempt + 1))
        logger.error(f"Permanently dropping {len(batch)} records after 3 failed attempts.")
        
    async def _flush_remaining(self):
        """Ensures any remaining records in the queue are persisted during shutdown."""
        if self._queue is None:
            return
            
        batch = []
        while not self._queue.empty():
            try:
                item = self._queue.get_nowait()
                batch.append(item)
                self._queue.task_done()
            except Exception:
                break
        
        if batch:
            logger.info(f"Flushing final {len(batch)} records to database...")
            await self._write_batch(batch)
