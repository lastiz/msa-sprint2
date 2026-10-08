from datetime import UTC, datetime
from decimal import Decimal
from typing import List, Protocol
from uuid import uuid4

from booking.entity import (
    Booking,
    BookingCreate,
    BookingOutbox,
    BookingRequest,
)


class IBookingRepository(Protocol):
    async def create(self, create: BookingCreate) -> Booking: ...
    async def list(self, user_id: str | None) -> List[Booking]: ...


class IBookingOutboxRepository(Protocol):
    async def add(self, outbox: BookingOutbox) -> None: ...


class IBookingServiceUOW(Protocol):
    @property
    def bookings(self) -> IBookingRepository: ...

    @property
    def booking_outbox(self) -> IBookingOutboxRepository: ...

    async def __aenter__(self) -> None: ...
    async def __aexit__(self, exc_type, exc_value, traceback) -> None: ...


class IMonolith(Protocol):
    async def is_user_active(self, user_id: str) -> bool: ...
    async def is_user_blacklisted(self, user_id: str) -> bool: ...
    async def is_hotel_operational(self, hotel_id: str) -> bool: ...
    async def is_hotel_trusted(self, hotel_id: str) -> bool: ...
    async def is_hotel_fully_booked(self, hotel_id: str) -> bool: ...
    async def is_user_vip(self, user_id: str) -> bool: ...
    async def discount(self, code: str, user_id: str) -> Decimal: ...


class BookingServiceError(BaseException): ...


class BookingRejected(BookingServiceError): ...


class BookingService:
    def __init__(self, uow: IBookingServiceUOW, monolith: IMonolith) -> None:
        self._uow = uow
        self._monolith = monolith

    async def create(self, request: BookingRequest) -> Booking:
        if not await self._monolith.is_user_active(request.user_id):
            raise BookingRejected("User is inactive")

        if await self._monolith.is_user_blacklisted(request.user_id):
            raise BookingRejected("User is blacklisted")

        if not await self._monolith.is_hotel_operational(request.hotel_id):
            raise BookingRejected("Hotel is not operational")

        if not await self._monolith.is_hotel_trusted(request.hotel_id):
            raise BookingRejected("Hotel is not trusted based on reviews")

        if await self._monolith.is_hotel_fully_booked(request.hotel_id):
            raise BookingRejected("Hotel is fully booked")

        base = Decimal(80 if await self._monolith.is_user_vip(request.user_id) else 100)
        discount = (
            await self._monolith.discount(request.promo_code, request.user_id)
            if request.promo_code is not None
            else Decimal(0)
        )
        price = base - discount
        created_at = datetime.now(UTC)

        async with self._uow:
            booking = await self._uow.bookings.create(
                BookingCreate(
                    user_id=request.user_id,
                    hotel_id=request.hotel_id,
                    promo_code=request.promo_code,
                    discount_percent=discount,
                    price=price,
                    created_at=created_at,
                )
            )
            uuid = uuid4()
            await self._uow.booking_outbox.add(
                BookingOutbox(
                    uuid=uuid,
                    payload={
                        "uuid": str(uuid),
                        "booking_id": booking.id,
                        "user_id": booking.user_id,
                        "hotel_id": booking.hotel_id,
                        "promo_code": booking.promo_code,
                        "discount_percent": float(booking.discount_percent),
                        "price": float(booking.price),
                        "created_at": booking.created_at.isoformat(),
                    },
                )
            )
        return booking

    async def list(self, user_id: str | None = None) -> List[Booking]:
        return await self._uow.bookings.list(user_id)
