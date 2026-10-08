from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class KafkaConfig(BaseModel):
    servers: str = "kafka:9092"
    topic: str = "booking.created"


class GrpcConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = Field(default=9090, ge=1, le=65535)


class OutboxConfig(BaseModel):
    poll_interval: float = Field(default=1, gt=0)


class AppConfig(BaseSettings):
    database_url: str
    monolith_url: str = "http://monolith:8080"
    http_timeout: float = Field(default=3, gt=0)
    kafka: KafkaConfig = Field(default_factory=KafkaConfig)
    grpc: GrpcConfig = Field(default_factory=GrpcConfig)
    outbox: OutboxConfig = Field(default_factory=OutboxConfig)
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_nested_delimiter="__",
    )


CONFIG = AppConfig.model_validate({})
