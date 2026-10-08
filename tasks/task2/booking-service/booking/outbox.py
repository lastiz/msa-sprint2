import asyncio
from datetime import UTC, datetime
from typing import List, Protocol

from dishka import AsyncContainer
from faststream.kafka import KafkaBroker

from booking.config import AppConfig
from booking.entity import BookingOutbox
from booking.logger import logger


class IBookingOutboxRepository(Protocol):
    async def add(self, outbox: BookingOutbox) -> None: ...
    async def claim_for_publish(self, limit: int = 1) -> List[BookingOutbox]: ...
    async def update_many(self, outboxes: list[BookingOutbox]) -> None: ...


class IOutboxWorkerUOW(Protocol):
    @property
    def booking_outbox(self) -> IBookingOutboxRepository: ...

    async def __aenter__(self) -> None: ...
    async def __aexit__(self, exc_type, exc_value, traceback) -> None: ...


class OutboxWorker:
    def __init__(
        self,
        config: AppConfig,
        container: AsyncContainer,
        broker: KafkaBroker,
    ) -> None:
        self._config = config
        self._container = container
        self._broker = broker

    async def publish(self, uow: IOutboxWorkerUOW) -> bool:
        async with uow:
            outboxes = await uow.booking_outbox.claim_for_publish(limit=1)
            now = datetime.now(UTC)

            if not outboxes:
                return False

            for outbox in outboxes:
                await self._broker.publish(
                    outbox.payload, topic=self._config.kafka.topic
                )
                outbox.published_at = now

            await uow.booking_outbox.update_many(outboxes)

        return True

    async def run(self) -> None:
        delay = self._config.outbox.poll_interval

        while True:
            try:
                async with self._container() as scope:
                    uow = await scope.get(IOutboxWorkerUOW)

                    if not await self.publish(uow):
                        await asyncio.sleep(delay)

            except Exception as e:
                logger.exception(
                    "Outbox delivery failed. Event remains pending", exc_info=e
                )
                await asyncio.sleep(delay)
