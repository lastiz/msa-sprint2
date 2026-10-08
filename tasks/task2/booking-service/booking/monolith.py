from decimal import Decimal
from urllib.parse import quote

import httpx
from pydantic import BaseModel, ValidationError


class PromoResponse(BaseModel):
    discount: Decimal


class MonolithError(Exception): ...


class Monolith:
    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def is_user_active(self, user_id: str) -> bool:
        return await self._request_bool(f"/api/users/{quote(user_id, safe='')}/active")

    async def is_user_blacklisted(self, user_id: str) -> bool:
        return await self._request_bool(
            f"/api/users/{quote(user_id, safe='')}/blacklisted"
        )

    async def is_hotel_operational(self, hotel_id: str) -> bool:
        return await self._request_bool(
            f"/api/hotels/{quote(hotel_id, safe='')}/operational"
        )

    async def is_hotel_trusted(self, hotel_id: str) -> bool:
        return await self._request_bool(
            f"/api/reviews/hotel/{quote(hotel_id, safe='')}/trusted"
        )

    async def is_hotel_fully_booked(self, hotel_id: str) -> bool:
        return await self._request_bool(
            f"/api/hotels/{quote(hotel_id, safe='')}/fully-booked"
        )

    async def is_user_vip(self, user_id: str) -> bool:
        response = await self._request(
            "GET", f"/api/users/{quote(user_id, safe='')}/status"
        )
        if response.status_code == 404:
            return False
        if response.status_code != 200:
            raise MonolithError("Unexpected response status")
        return response.text.upper() == "VIP"

    async def discount(self, code: str, user_id: str) -> Decimal:
        response = await self._request(
            "POST",
            "/api/promos/validate",
            params={"code": code, "userId": user_id},
        )
        if response.status_code == 400:
            return Decimal(0)
        if response.status_code != 200:
            raise MonolithError("Unexpected promo response")
        try:
            return PromoResponse.model_validate_json(response.content).discount
        except ValidationError as e:
            raise MonolithError("Invalid promo response") from e

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        try:
            return await self._http.request(method, path, **kwargs)
        except httpx.HTTPError as e:
            raise MonolithError("Request failed") from e

    async def _request_bool(self, path: str) -> bool:
        response = await self._request("GET", path)
        if response.status_code != 200:
            raise MonolithError("Unexpected response status")
        try:
            value = response.json()
        except ValueError as e:
            raise MonolithError("Invalid boolean response") from e
        if type(value) is not bool:
            raise MonolithError("Invalid boolean response")
        return value
