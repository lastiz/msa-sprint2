from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from booking_history.entity import BookingHistory


### Models
class BaseModel(DeclarativeBase): ...


class BookingHistoryModel(BaseModel):
    __tablename__ = "booking_history"

    uuid: Mapped[UUID] = mapped_column(primary_key=True)
    booking_id: Mapped[int]
    user_id: Mapped[str] = mapped_column(String(128))
    hotel_id: Mapped[str] = mapped_column(String(128))
    promo_code: Mapped[str | None] = mapped_column(String(128))
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    price: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=UTC),
    )


### Repositories
class BookingHistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, history: BookingHistory) -> bool:
        async with self._session.begin():
            statement = (
                insert(BookingHistoryModel)
                .values(history.model_dump())
                .on_conflict_do_nothing(index_elements=[BookingHistoryModel.uuid])
                .returning(BookingHistoryModel.uuid)
            )
            uuid = (await self._session.execute(statement)).scalar_one_or_none()

        return bool(uuid)
