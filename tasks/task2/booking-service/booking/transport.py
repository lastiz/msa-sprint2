from dishka import AsyncContainer
from grpclib import GRPCError, Status
from pydantic import ValidationError

from booking.entity import Booking, BookingRequest
from booking.generated import booking as rpc
from booking.logger import logger
from booking.service import BookingRejected, BookingService


def from_booking_entity_to_rpc_model(booking: Booking) -> rpc.BookingResponse:
    return rpc.BookingResponse(
        id=str(booking.id),
        user_id=booking.user_id,
        hotel_id=booking.hotel_id,
        promo_code=booking.promo_code or "",
        discount_percent=float(booking.discount_percent),
        price=float(booking.price),
        created_at=booking.created_at.isoformat(),
    )


class BookingGrpcService(rpc.BookingServiceBase):
    def __init__(self, container: AsyncContainer) -> None:
        self._container = container

    async def create_booking(
        self, booking_request: rpc.BookingRequest
    ) -> rpc.BookingResponse:
        try:
            request = BookingRequest.model_validate(
                booking_request, from_attributes=True
            )

        except ValidationError as e:
            raise GRPCError(
                Status.INVALID_ARGUMENT, "Invalid create booking request"
            ) from e

        try:
            async with self._container() as scope:
                service = await scope.get(BookingService)
                booking = await service.create(request)

        except BookingRejected as e:
            raise GRPCError(Status.FAILED_PRECONDITION, str(e)) from e

        except Exception as e:
            logger.exception("Booking create request failed", exc_info=e)
            raise GRPCError(Status.INTERNAL, "Internal error") from e

        return from_booking_entity_to_rpc_model(booking)

    async def list_bookings(
        self, booking_list_request: rpc.BookingListRequest
    ) -> rpc.BookingListResponse:
        user_id = booking_list_request.user_id

        if not user_id:
            raise GRPCError(Status.INVALID_ARGUMENT, "Invalid list booking request")

        try:
            async with self._container() as scope:
                service = await scope.get(BookingService)
                bookings = await service.list(user_id)

        except Exception as e:
            logger.exception("Booking list request failed", exc_info=e)
            raise GRPCError(Status.INTERNAL, "Internal error") from e

        return rpc.BookingListResponse(
            bookings=[from_booking_entity_to_rpc_model(item) for item in bookings]
        )
