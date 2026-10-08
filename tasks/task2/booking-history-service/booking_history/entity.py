from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class BookingHistory(BaseModel):
    uuid: UUID
    booking_id: int
    user_id: str
    hotel_id: str
    promo_code: str | None = None
    discount_percent: Decimal
    price: Decimal
    created_at: datetime
    received_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))

    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True,
        from_attributes=True,
    )
