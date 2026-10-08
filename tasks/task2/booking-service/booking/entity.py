from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class BookingRequest(BaseModel):
    user_id: str
    hotel_id: str
    promo_code: str | None


class BookingCreate(BaseModel):
    user_id: str
    hotel_id: str
    promo_code: str | None
    discount_percent: Decimal
    price: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Booking(BookingCreate):
    id: int


class BookingCreated(BaseModel):
    uuid: UUID = Field(default_factory=uuid4)
    booking_id: int
    user_id: str
    hotel_id: str
    promo_code: str | None
    discount_percent: Decimal
    price: Decimal
    created_at: datetime

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class BookingOutbox(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: UUID = Field(default_factory=uuid4)
    payload: dict
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    published_at: datetime | None = None
