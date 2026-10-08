import logging

from booking.config import CONFIG

logging.basicConfig(
    level=logging.DEBUG if CONFIG.debug else logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("booking-service")
