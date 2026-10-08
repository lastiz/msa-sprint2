from contextlib import asynccontextmanager
from typing import AsyncIterator

from dishka import Provider, Scope, make_async_container, provide
from dishka_faststream import FromDishka, inject
from dishka_faststream import setup_dishka as faststream_integration
from faststream import AckPolicy, FastStream
from faststream.kafka import KafkaBroker, KafkaMessage, KafkaRouter
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from booking_history.config import CONFIG
from booking_history.logger import logger
from booking_history.service import BookingHistoryService, IBookingHistoryRepository
from booking_history.storage import BaseModel, BookingHistoryRepository


### DI Container's Provider
class AppProvider(Provider):

    @provide(scope=Scope.APP)
    async def engine(self) -> AsyncIterator[AsyncEngine]:
        engine = create_async_engine(CONFIG.database_url, pool_pre_ping=True)

        try:
            yield engine

        finally:
            await engine.dispose()

    @provide(scope=Scope.APP)
    async def sessionmaker(
        self, engine: AsyncEngine
    ) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(
            engine,
            autocommit=False,
            expire_on_commit=False,
            class_=AsyncSession,
        )

    @provide(scope=Scope.REQUEST)
    async def session(
        self, sessionmaker: async_sessionmaker[AsyncSession]
    ) -> AsyncIterator[AsyncSession]:
        async with sessionmaker() as session:
            yield session

    @provide(scope=Scope.REQUEST)
    async def booking_history_repository(
        self, session: AsyncSession
    ) -> IBookingHistoryRepository:
        return BookingHistoryRepository(session)

    @provide(scope=Scope.REQUEST)
    async def booking_history_service(
        self, repository: IBookingHistoryRepository
    ) -> BookingHistoryService:
        return BookingHistoryService(repository)


### APP
router = KafkaRouter()


@router.subscriber(
    CONFIG.kafka.topic,
    group_id=CONFIG.kafka.group_id,
    ack_policy=AckPolicy.NACK_ON_ERROR,
)
@inject
async def consume_booking_history(
    msg: KafkaMessage, service: FromDishka[BookingHistoryService]
) -> None:
    await service.record(msg.body)


def create_app() -> FastStream:
    container = make_async_container(AppProvider())
    broker = KafkaBroker(bootstrap_servers=CONFIG.kafka.servers, logger=logger)
    broker.include_router(router)

    @asynccontextmanager
    async def lifespan():
        engine = await container.get(AsyncEngine)
        async with engine.begin() as session:
            await session.run_sync(BaseModel.metadata.create_all)
        yield

    app = FastStream(broker, lifespan=lifespan)
    faststream_integration(container, app)
    return app
