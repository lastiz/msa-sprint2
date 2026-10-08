import json
from datetime import UTC, datetime
from typing import Protocol

from booking_history.entity import BookingHistory
from booking_history.logger import logger


class IBookingHistoryRepository(Protocol):
    async def add(self, history: BookingHistory) -> bool: ...


class BookingHistoryService:
    def __init__(self, storage: IBookingHistoryRepository) -> None:
        self._storage = storage

    async def record(self, body: bytes) -> None:
        if not (event := await self.validate(body)):
            return

        event.received_at = datetime.now(tz=UTC)

        if await self._storage.add(event):
            logger.debug(f"Event saved: {event.uuid}")
        else:
            logger.warning(f"Got deplicated event: {event.uuid}")

    async def validate(self, body: bytes) -> BookingHistory | None:
        event: BookingHistory | None = None

        try:
            data = json.loads(body)
            event = BookingHistory.model_validate(data)

        except Exception as e:
            logger.error(f"Got invalid event. Body: {body}. Error: {e}")

        return event
