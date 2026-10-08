from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class KafkaConfig(BaseModel):
    servers: str
    topic: str = "booking.created"
    group_id: str = "booking-history-v1"


class AppConfig(BaseSettings):
    database_url: str
    kafka: KafkaConfig
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        str_strip_whitespace=True,
        env_nested_delimiter="__",
    )


CONFIG = AppConfig.model_validate({})
