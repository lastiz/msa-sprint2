from datetime import UTC, datetime
from decimal import Decimal
from typing import List
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, Numeric, String, select, update
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from booking.entity import Booking, BookingCreate, BookingOutbox


### Models
class BaseModel(DeclarativeBase): ...


class BookingModel(BaseModel):
    __tablename__ = "booking"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    hotel_id: Mapped[str] = mapped_column(String(128))
    promo_code: Mapped[str | None] = mapped_column(String(128))
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    price: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class BookingOutboxModel(BaseModel):
    __tablename__ = "booking_outbox"
    uuid: Mapped[UUID] = mapped_column(primary_key=True)
    payload: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )


### Repositories
class BookingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, create: BookingCreate) -> Booking:
        query = insert(BookingModel).values(create.model_dump()).returning(BookingModel)
        row = await self._session.scalar(query)
        return Booking.model_validate(row)

    async def list(self, user_id: str | None) -> List[Booking]:
        query = select(BookingModel).order_by(BookingModel.id)
        if user_id is not None:
            query = query.where(BookingModel.user_id == user_id)
        rows = await self._session.scalars(query)
        return [Booking.model_validate(row) for row in rows]


class BookingOutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, outbox: BookingOutbox) -> None:
        query = insert(BookingOutboxModel).values(outbox.model_dump())
        await self._session.execute(query)

    async def claim_for_publish(self, limit: int = 1) -> List[BookingOutbox]:
        query = (
            select(BookingOutboxModel)
            .where(BookingOutboxModel.published_at.is_(None))
            .order_by(BookingOutboxModel.created_at)
            .with_for_update(skip_locked=True)
            .limit(limit)
        )
        rows = await self._session.scalars(query)
        return [BookingOutbox.model_validate(row) for row in rows]

    async def update_many(self, outboxes: list[BookingOutbox]) -> None:
        if not outboxes:
            return

        query = update(BookingOutboxModel)
        await self._session.execute(query, [outbox.model_dump() for outbox in outboxes])


class UOW:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @property
    def bookings(self) -> BookingRepository:
        return BookingRepository(self._session)

    @property
    def booking_outbox(self) -> BookingOutboxRepository:
        return BookingOutboxRepository(self._session)

    async def __aenter__(self) -> None:
        await self._session.begin()

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        if exc_value is None:
            await self._session.commit()
        else:
            await self._session.rollback()
