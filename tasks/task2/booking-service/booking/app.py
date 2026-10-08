import asyncio
import signal
from collections.abc import AsyncIterator
from contextlib import suppress

import httpx
from dishka import AnyOf, Provider, Scope, make_async_container, provide
from faststream.kafka import KafkaBroker
from grpclib.server import Server
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from booking.config import CONFIG
from booking.logger import logger
from booking.monolith import Monolith
from booking.outbox import IOutboxWorkerUOW, OutboxWorker
from booking.service import (
    BookingService,
    IBookingServiceUOW,
    IMonolith,
)
from booking.storage import UOW, BaseModel
from booking.transport import BookingGrpcService


class AppProvider(Provider):
    @provide(scope=Scope.APP)
    async def engine(self) -> AsyncIterator[AsyncEngine]:
        engine = create_async_engine(
            CONFIG.database_url,
            pool_pre_ping=True,
        )
        try:
            yield engine
        finally:
            await engine.dispose()

    @provide(scope=Scope.APP)
    def sessionmaker(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(
            engine,
            autocommit=False,
            expire_on_commit=False,
            class_=AsyncSession,
        )

    @provide(scope=Scope.APP)
    async def monolith(self) -> AsyncIterator[IMonolith]:
        async with httpx.AsyncClient(
            base_url=CONFIG.monolith_url, timeout=CONFIG.http_timeout
        ) as client:
            yield Monolith(client)

    @provide(scope=Scope.REQUEST)
    async def session(
        self, sessions: async_sessionmaker[AsyncSession]
    ) -> AsyncIterator[AsyncSession]:
        async with sessions() as session:
            yield session

    @provide(scope=Scope.REQUEST)
    def uow(self, session: AsyncSession) -> AnyOf[IBookingServiceUOW, IOutboxWorkerUOW]:
        return UOW(session)

    @provide(scope=Scope.REQUEST)
    def service(self, uow: IBookingServiceUOW, monolith: IMonolith) -> BookingService:
        return BookingService(uow, monolith)


async def init_database_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(BaseModel.metadata.create_all)


async def run_app() -> None:
    container = make_async_container(AppProvider())
    server = Server([BookingGrpcService(container)])
    broker = KafkaBroker(
        bootstrap_servers=CONFIG.kafka.servers,
        logger=logger,
        acks="all",
        enable_idempotence=True,
    )
    uow_worker = OutboxWorker(CONFIG, container, broker)
    stopping = asyncio.Event()
    loop = asyncio.get_running_loop()
    signals = (signal.SIGINT, signal.SIGTERM)

    for sig in signals:
        loop.add_signal_handler(sig, stopping.set)

    worker_task = None
    started = False

    try:
        await init_database_schema(await container.get(AsyncEngine))
        await broker.start()
        await server.start(CONFIG.grpc.host, CONFIG.grpc.port)
        started = True
        worker_task = asyncio.create_task(uow_worker.run())
        logger.info(f"Booking gRPC listening on {CONFIG.grpc.host}:{CONFIG.grpc.port}")
        await stopping.wait()

    finally:
        try:
            if started:
                server.close()
                await server.wait_closed()

            if worker_task is not None:
                with suppress(asyncio.CancelledError):
                    worker_task.cancel()
                    await worker_task

            await broker.stop()

        finally:
            await container.close()

            for sig in signals:
                loop.remove_signal_handler(sig)
